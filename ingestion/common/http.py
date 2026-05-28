"""Shared HTTP client with retry/backoff — reused by every live API extractor."""

from __future__ import annotations

import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)


def make_session(api_key: str | None = None, api_key_header: str = "X-API-Key") -> requests.Session:
    """Return a requests Session that retries idempotent calls with exponential backoff."""
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1.0,  # 1s, 2s, 4s, 8s, 16s
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    if api_key:
        session.headers.update({api_key_header: api_key})
    return session


def get_json(session: requests.Session, url: str, params: dict | None = None, timeout: int = 30):
    resp = session.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()
