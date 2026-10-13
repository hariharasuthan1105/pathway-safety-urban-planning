"""Bounded startup wait for isolated CI services, never for deployment."""
import sys
import time
from urllib.request import urlopen

for url in sys.argv[1:]:
    for attempt in range(30):
        try:
            with urlopen(url, timeout=2) as response:
                assert response.status == 200
            break
        except Exception:
            if attempt == 29:
                raise RuntimeError(f'QA service did not start: {url}') from None
            time.sleep(1)
