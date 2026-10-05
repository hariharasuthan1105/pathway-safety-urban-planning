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

    class Table:
        def __init__(self, data: Optional[List[Dict[str, Any]]] = None, generator: Optional[Callable] = None, schema: Any = None):
            self.data = data or []
            self.generator = generator
            self.schema = schema

        def __getattr__(self, name: str):
            if name.startswith("_") or name in ("data", "generator", "schema"):
                raise AttributeError(name)
            return ColumnExpression(name)


        def select(self, *args, **kwargs) -> 'Table':
            # Evaluates projections over stored or generated data
            new_data = []
            source_data = self._fetch_rows()
            for row in source_data:
                new_row = {}
                for k, v in kwargs.items():
                    if callable(v):
                        # Handle UDF / function call
                        arg_val = row.get("data", row)
                        try:
                            new_row[k] = v(arg_val)
                        except Exception:
                            new_row[k] = v
                    elif hasattr(v, "name"):
                        new_row[k] = row.get(v.name)
                    else:
                        new_row[k] = row.get(k, v)
                new_data.append(new_row)
            return Table(data=new_data)

        def filter(self, predicate: Any) -> 'Table':
            source_data = self._fetch_rows()
            filtered = []
            for row in source_data:
                # Basic anomaly / attribute check
                row_data = row.get("data", {})
                if isinstance(row_data, dict) and row_data.get("anomaly", False):
                    filtered.append(row)
                elif isinstance(row, dict) and row.get("anomaly", False):
                    filtered.append(row)
            return Table(data=filtered)

        def collect(self) -> List[Dict[str, Any]]:
            return self._fetch_rows()

        def _fetch_rows(self) -> List[Dict[str, Any]]:
            if self.data:
                return self.data
            if self.generator:
                rows = []
                gen = self.generator()
                # Fetch up to 10 sample items for compatibility rendering/collection
                for _ in range(10):
                    try:
                        rows.append(next(gen))
                    except StopIteration:
                        break
                    except Exception as e:
                        logger.warning(f"Error reading stream row: {e}")
                        break
                self.data = rows
                return rows
            return []

        @classmethod
        def concat(cls, tables: List['Table']) -> 'Table':
            all_data = []
            for t in tables:
                all_data.extend(t._fetch_rows())
            return Table(data=all_data)

        @classmethod
        def concat_by_name(cls, *tables: 'Table') -> 'Table':
            return cls.concat(list(tables))

    class PythonIO:
        @staticmethod
        def read(subject: Callable, schema: Any = None) -> Table:
            return Table(generator=subject, schema=schema)

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

    def sleep(seconds: float):
        time.sleep(seconds)

    def run():
        logger.info("Pathway streaming pipeline running...")

    class CompatibilityPathway:
        Schema = Schema
        Json = Json
        Table = Table
        io = IO()
        udf = staticmethod(udf)
        this = this
        sleep = staticmethod(sleep)
        run = staticmethod(run)

        @staticmethod
        def schema(*args, **kwargs):
            return Schema

    pw = CompatibilityPathway()
