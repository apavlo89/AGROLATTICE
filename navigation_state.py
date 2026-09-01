"""Safe programmatic navigation helpers for Streamlit command-centre widgets.

Streamlit widget values with explicit ``key=`` entries own their session-state
slot after instantiation. Programmatic navigation that mutates a *different*
mirror key can therefore be silently undone on the next rerun when the widget
restores its persisted value. Mutating the widget key after instantiation can
also raise StreamlitAPIException.

This module uses a two-phase route request:
1. A button queues a target in a non-widget request key and reruns.
2. At the beginning of the next run, before the navigation widget is created,
   the request is consumed and copied safely into the widget state.

The functions are intentionally independent of Streamlit so the state-machine
behaviour can be regression-tested offline.
"""
from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from typing import Any

MODULE_VERSION = "1.0.0"


def queue_view_request(
    state: MutableMapping[str, Any],
    *,
    request_key: str,
    target: str,
    notice_key: str | None = None,
    notice: Any | None = None,
) -> None:
    """Queue a view change without mutating an already-instantiated widget key."""
    state[request_key] = str(target)
    if notice_key is not None:
        if notice is None:
            state.pop(notice_key, None)
        else:
            state[notice_key] = notice


def consume_view_request(
    state: MutableMapping[str, Any],
    *,
    request_key: str,
    widget_key: str,
    options: Sequence[str],
    default: str,
    mirror_key: str | None = None,
) -> str:
    """Resolve and safely apply a queued navigation request before widget creation."""
    valid = [str(item) for item in options]
    fallback = str(default) if str(default) in valid else valid[0]

    requested = state.pop(request_key, None)
    if requested in valid:
        state[widget_key] = requested
        if mirror_key:
            state[mirror_key] = requested

    current = state.get(widget_key)
    if current not in valid and mirror_key:
        current = state.get(mirror_key)
    if current not in valid:
        current = fallback

    # This assignment is safe only because callers invoke this helper before
    # creating the widget in the current Streamlit run.
    state[widget_key] = current
    if mirror_key:
        state[mirror_key] = current
    return str(current)
