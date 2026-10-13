"""Canonical source classification and evidence status used in API envelopes."""
from enum import Enum


class SourceClass(str, Enum):
    REAL = 'REAL'
    SIMULATED = 'SIMULATED'
    WEBHOOK = 'WEBHOOK'
    DERIVED = 'DERIVED'
    NOT_CONFIGURED = 'NOT_CONFIGURED'


class SourceStatus(str, Enum):
    LIVE = 'LIVE'
    SIMULATED = 'SIMULATED'
    STALE = 'STALE'
    DEGRADED = 'DEGRADED'
    OFFLINE = 'OFFLINE'
    NOT_CONFIGURED = 'NOT_CONFIGURED'


def source_class(source, mode=''):
    if mode == 'NOT_CONFIGURED' or source in {'tomtom_traffic', 'google_traffic'}:
        return SourceClass.NOT_CONFIGURED.value
    if mode == 'SIMULATED' or source in {'twitter', 'police_scanner', 'city_sensors'} or 'simulation' in source:
        return SourceClass.SIMULATED.value
    if source in {'webhook_api', 'webhook_ingestion'}:
        return SourceClass.WEBHOOK.value
    return SourceClass.REAL.value


def evidence_envelope(source, entry):
    result = dict(entry)
    result['source_class'] = source_class(source, entry.get('mode', ''))
    result['ingested_at'] = entry.get('received_at')
    status = entry.get('status')
    if status not in {item.value for item in SourceStatus}:
        status = 'OFFLINE'
    if status == 'LIVE' and result['source_class'] == 'SIMULATED':
        status = 'SIMULATED'
    result['status'] = status
    result['unavailable_reason'] = None if entry.get('observed_at') else (
        'Source is not configured' if status == 'NOT_CONFIGURED' else 'No observation received')
    return result
