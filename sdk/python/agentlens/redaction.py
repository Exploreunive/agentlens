from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Mapping

EMAIL_RE = re.compile(r'([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})')
PHONE_RE = re.compile(r'\b(?:\+?\d{1,3}[\s-]?)?(?:1[3-9]\d|\d{3})[\s-]?\d{4}[\s-]?\d{4}\b')
TOKEN_RE = re.compile(r'\b(?:sk-|ghp_|gho_|ghu_|github_pat_|rk-)[A-Za-z0-9_\-]{8,}\b')


def redact_string(value: str) -> str:
    value = EMAIL_RE.sub('[redacted_email]', value)
    value = PHONE_RE.sub('[redacted_phone]', value)
    value = TOKEN_RE.sub('[redacted_secret]', value)
    return value


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_string(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return [redact_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): redact_value(item) for key, item in value.items()}
    return value


def redact_payload(payload: Dict[str, Any] | None, sensitive_keys: Iterable[str] = ()) -> Dict[str, Any]:
    payload = payload or {}
    sensitive = {key.lower() for key in sensitive_keys}
    redacted: Dict[str, Any] = {}
    for key, value in payload.items():
        if str(key).lower() in sensitive:
            redacted[key] = '[redacted]'
        else:
            redacted[key] = redact_value(value)
    return redacted
