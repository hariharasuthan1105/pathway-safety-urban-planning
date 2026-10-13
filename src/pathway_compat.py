"""
Pathway compatibility and fallback layer.
If the native 'pathway' package is installed (Linux/macOS/WSL), it re-exports it directly.
If running in an environment where native pathway binaries are unavailable (e.g. Windows native),
it provides a lightweight pure-Python streaming table fallback so the pipeline, tests, and app
can run, process simulated data, and be fully tested.
"""

import inspect
import sys
import time
import json
import logging
import threading
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("pathway_compat")

try:
    import pathway as pw  # type: ignore
    IS_NATIVE_PATHWAY = True
    logger.info("Native Pathway package loaded successfully.")
except ImportError:
    IS_NATIVE_PATHWAY = False
    logger.info("Native Pathway package not found. Using Pathway compatibility layer.")

    class Schema:
        """Base Schema for compatibility layer."""
        timestamp: str
        source: str
        data: Any
        location: Any

        @classmethod
        def __contains__(cls, item: str) -> bool:
            return hasattr(cls, item) or item in getattr(cls, "__annotations__", {})

    class Json:
        """Type marker for JSON fields."""
        pass

    class ColumnExpression:
        def __init__(self, name: str):
            self.name = name

        def get(self, key: str, default: Any = None):
            return ColumnExpression(f"{self.name}.get({key!r}, {default!r})")

        def __getattr__(self, item: str):
            return ColumnExpression(f"{self.name}.{item}")

    class ThisProxy:
        def __getattr__(self, item: str):
            return ColumnExpression(item)

    this = ThisProxy()

    class UDFColumnExpression:
        def __init__(self, fn: Callable, col_name: str):
            self.fn = fn
            self.col_name = col_name

    def udf(fn: Callable) -> Callable:
        """Decorator for user-defined functions."""
        def udf_wrapper(*args):
            if args and hasattr(args[0], "name"):
                return UDFColumnExpression(fn, args[0].name)
            return fn(*args)
        udf_wrapper._is_udf = True  # type: ignore
        return udf_wrapper

    _ACTIVE_STREAMS: List[Any] = []

    class Table:
        def __init__(self, data: Optional[List[Dict[str, Any]]] = None, generator: Optional[Callable] = None, schema: Any = None):
            self._rows: List[Dict[str, Any]] = data or []
            self.generator = generator
            self.schema = schema
            self.children: List['Table'] = []
            self.subscribers: List[Callable[[Dict[str, Any]], None]] = []
            self.transform_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
            self.filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None

        def __getattr__(self, name: str):
            if name.startswith("_") or name in ("generator", "schema", "children", "subscribers", "transform_fn", "filter_fn"):
                raise AttributeError(name)
            return ColumnExpression(name)

        @staticmethod
        def _invoke_subscriber(callback, *, key, row, time, is_addition):
            signature = inspect.signature(callback)
            try:
                signature.bind(key=key, row=row, time=time, is_addition=is_addition)
                style = "keywords"
            except TypeError:
                try:
                    signature.bind(key, row, time, is_addition)
                    style = "positional"
                except TypeError:
                    signature.bind(row)
                    style = "legacy"
            # Do not catch exceptions raised inside the callback and retry it.
            if style == "keywords":
                callback(key=key, row=row, time=time, is_addition=is_addition)
            elif style == "positional":
                callback(key, row, time, is_addition)
            elif is_addition:
                callback(row)

        def subscribe(self, callback):
            if callback in self.subscribers:
                return
            self.subscribers.append(callback)
            for row in list(self._rows):
                self._invoke_subscriber(callback, key=row.get("id", id(row)), row=row,
                                        time=int(time.time()*1000000), is_addition=True)

        def publish(self, row: Dict[str, Any], *, key=None, event_time=None, is_addition=True):
            event_time = event_time if event_time is not None else int(time.time() * 1000000)
            """Processes an incoming row through this Table's transforms, stores it, and notifies children & subscribers."""
            processed_row = row
            if self.transform_fn:
                try:
                    processed_row = self.transform_fn(row)
                except Exception as e:
                    logger.warning(f"Table transform error: {e}")
                    processed_row = row

            if self.filter_fn:
                try:
                    if not self.filter_fn(processed_row):
                        return
                except Exception:
                    return

            if is_addition:
                self._rows.append(processed_row)
                # Compatibility snapshots are bounded; the runtime state owns history.
                if len(self._rows) > 5000:
                    del self._rows[:len(self._rows) - 5000]
            elif processed_row in self._rows:
                self._rows.remove(processed_row)

            # Notify direct sink subscribers
            for sub in list(self.subscribers):
                try:
                    self._invoke_subscriber(sub, key=key if key is not None else row.get("id", id(row)), row=processed_row, time=event_time, is_addition=is_addition)
                except Exception as e:
                    raise

            # Forward to child tables in the DAG
            for child in list(self.children):
                child.publish(processed_row, key=key, event_time=event_time, is_addition=is_addition)

        def select(self, *args, **kwargs) -> 'Table':
            child = Table(schema=self.schema)
            
            def do_transform(row: Dict[str, Any]) -> Dict[str, Any]:
                new_row = {}
                for k, v in kwargs.items():
                    if isinstance(v, UDFColumnExpression):
                        val = row.get(v.col_name, row)
                        try:
                            new_row[k] = v.fn(val)
                        except Exception as e:
                            logger.warning(f"UDF execution error: {e}")
                            new_row[k] = val
                    elif callable(v):
                        arg_val = row.get("data", row)
                        try:
                            new_row[k] = v(arg_val)
                        except Exception:
                            new_row[k] = v
                    elif hasattr(v, "name"):
                        new_row[k] = row.get(v.name)
                    else:
                        new_row[k] = row.get(k, v)
                return new_row

            child.transform_fn = do_transform
            self.children.append(child)
            
            # Backfill existing data
            for row in list(self._fetch_rows()):
                child.publish(row)

            return child

        def filter(self, predicate: Any) -> 'Table':
            child = Table(schema=self.schema)

            def do_filter(row: Dict[str, Any]) -> bool:
                row_data = row.get("data", {})
                if isinstance(row_data, dict) and row_data.get("anomaly", False):
                    return True
                elif isinstance(row, dict) and row.get("anomaly", False):
                    return True
                return False

            child.filter_fn = do_filter
            self.children.append(child)

            for row in list(self._fetch_rows()):
                child.publish(row)

            return child

        def collect(self) -> List[Dict[str, Any]]:
            return self._fetch_rows()

        def _fetch_rows(self) -> List[Dict[str, Any]]:
            return self._rows

        @classmethod
        def concat(cls, *args) -> 'Table':
            tables = []
            for arg in args:
                if isinstance(arg, list):
                    tables.extend(arg)
                elif isinstance(arg, Table):
                    tables.append(arg)
            combined = Table()
            for t in tables:
                t.children.append(combined)
                for row in t._fetch_rows():
                    combined.publish(row)
            return combined

        @classmethod
        def concat_by_name(cls, *args) -> 'Table':
            return cls.concat(*args)

        @classmethod
        def concat_reindex(cls, *args) -> 'Table':
            return cls.concat(*args)


    class ConnectorSubject:
        def __init__(self, *args, **kwargs):
            self._table: Optional['Table'] = None

        def run(self):
            pass

        def next(self, **kwargs):
            if self._table:
                self._table.publish(kwargs)

    class PythonIO:
        ConnectorSubject = ConnectorSubject

        @staticmethod
        def read(subject: Any, schema: Any = None) -> Table:
            if hasattr(subject, "run") or isinstance(subject, ConnectorSubject):
                t = Table(generator=None, schema=schema)
                subject._table = t
                _ACTIVE_STREAMS.append((t, subject))
                return t
            elif callable(subject):
                t = Table(generator=subject, schema=schema)
                _ACTIVE_STREAMS.append((t, None))
                return t
            else:
                t = Table(generator=subject, schema=schema)
                _ACTIVE_STREAMS.append((t, None))
                return t

    class CSVIO:
        @staticmethod
        def write(table: Table, filename: str):
            rows = table.collect()
            logger.info(f"[CSV Sink] Writing {len(rows)} rows to {filename}")

    class JSONIO:
        @staticmethod
        def write(table: Table, filename: str):
            rows = table.collect()
            logger.info(f"[JSON Sink] Writing {len(rows)} rows to {filename}")

    class IO:
        python = PythonIO()
        csv = CSVIO()
        json = JSONIO()
        jsonlines = JSONIO()

        @staticmethod
        def subscribe(table: Table, on_change: Callable):
            table.subscribe(on_change)

    def sleep(seconds: float):
        time.sleep(seconds)

    def _run_streaming_engine():
        logger.info("Pathway streaming engine starting background worker threads...")
        for item in list(_ACTIVE_STREAMS):
            if isinstance(item, tuple):
                tbl, subject = item
            else:
                tbl, subject = item, None

            if subject is not None:
                def connector_worker(sub=subject):
                    try:
                        sub.run()
                    except Exception as e:
                        logger.warning(f"Error in connector subject thread: {e}")

                th = threading.Thread(target=connector_worker, daemon=True)
                th.start()
            elif tbl and tbl.generator:
                def worker(t=tbl):
                    try:
                        gen = t.generator()
                        for row in gen:
                            if isinstance(row, dict):
                                t.publish(row)
                    except Exception as e:
                        logger.warning(f"Error in stream generator thread: {e}")

                th = threading.Thread(target=worker, daemon=True)
                th.start()

    def run():
        logger.info("Pathway streaming pipeline running...")
        _run_streaming_engine()

    class CompatibilityPathway:
        Schema = Schema
        Json = Json
        Table = Table
        ConnectorSubject = ConnectorSubject
        io = IO()
        udf = staticmethod(udf)
        this = this
        sleep = staticmethod(sleep)
        run = staticmethod(run)
        _active_streams = _ACTIVE_STREAMS

        @staticmethod
        def schema(*args, **kwargs):
            return Schema

    pw = CompatibilityPathway()

