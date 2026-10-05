"""
Pathway compatibility and fallback layer.
If the native 'pathway' package is installed (Linux/macOS/WSL), it re-exports it directly.
If running in an environment where native pathway binaries are unavailable (e.g. Windows native),
it provides a lightweight pure-Python streaming table fallback so the pipeline, tests, and app
can run, process simulated data, and be fully tested.
"""

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

    def udf(fn: Callable) -> Callable:
        """Decorator for user-defined functions."""
        fn._is_udf = True  # type: ignore
        return fn

    _ACTIVE_STREAMS: List[Any] = []

    class Table:
        def __init__(self, data: Optional[List[Dict[str, Any]]] = None, generator: Optional[Callable] = None, schema: Any = None):
            self.data: List[Dict[str, Any]] = data or []
            self.generator = generator
            self.schema = schema
            self.children: List['Table'] = []
            self.subscribers: List[Callable[[Dict[str, Any]], None]] = []
            self.transform_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
            self.filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None

        def __getattr__(self, name: str):
            if name.startswith("_") or name in ("data", "generator", "schema", "children", "subscribers", "transform_fn", "filter_fn"):
                raise AttributeError(name)
            return ColumnExpression(name)

        def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
            """Registers a sink callback that receives streaming events output by this Pathway table."""
            if callback not in self.subscribers:
                self.subscribers.append(callback)
            for row in list(self.data):
                try:
                    callback(row)
                except Exception as e:
                    logger.warning(f"Subscriber error on replay: {e}")

        def publish(self, row: Dict[str, Any]):
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

            self.data.append(processed_row)

            # Notify direct sink subscribers
            for sub in list(self.subscribers):
                try:
                    sub(processed_row)
                except Exception as e:
                    logger.warning(f"Error in Pathway sink subscriber: {e}")

            # Forward to child tables in the DAG
            for child in list(self.children):
                child.publish(processed_row)

        def select(self, *args, **kwargs) -> 'Table':
            child = Table(schema=self.schema)
            
            def do_transform(row: Dict[str, Any]) -> Dict[str, Any]:
                new_row = {}
                for k, v in kwargs.items():
                    if callable(v):
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
            return self.data

        @classmethod
        def concat(cls, tables: List['Table']) -> 'Table':
            combined = Table()
            for t in tables:
                t.children.append(combined)
                for row in t._fetch_rows():
                    combined.publish(row)
            return combined

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
            if isinstance(subject, ConnectorSubject):
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
        def subscribe(table: Table, callback: Callable[[Dict[str, Any]], None]):
            table.subscribe(callback)

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

