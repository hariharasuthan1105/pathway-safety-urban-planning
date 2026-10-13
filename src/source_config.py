from urllib.parse import urlsplit


def valid_feed_url(value):
    """A GTFS connector is configured only with an absolute HTTP(S) feed URL."""
    try:
        parsed = urlsplit(value or '')
        return parsed.scheme in {'http', 'https'} and bool(parsed.hostname) and not (parsed.username or parsed.password)
    except ValueError:
        return False
