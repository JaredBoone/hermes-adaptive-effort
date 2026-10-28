"""Experimental Responses full-replay builder; deliberately not wired to middleware.

The caller must durably preserve and replay the returned input verbatim.  This
function cannot prove that the supplied history is complete or that a route
accepts the item; it is not a provider capability check.
"""
from typing import Any, Dict, Optional


_EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max"})


def build_full_replay_update(request: Dict[str, Any], target: str) -> Optional[Dict[str, Any]]:
    """Insert a transition before the final user item, retaining all prior items.

    Return None when this conservative builder cannot safely construct a replay.
    A caller must persist the entire returned history and its original baseline.
    """
    if not isinstance(request, dict) or target not in _EFFORTS:
        return None
    if request.get("previous_response_id") is not None:
        return None
    reasoning = request.get("reasoning")
    if not isinstance(reasoning, dict) or reasoning.get("effort") not in _EFFORTS:
        return None
    if reasoning.get("enabled") is False or reasoning.get("mode") in ("pro", "tournament"):
        return None
    history = request.get("input")
    if not isinstance(history, list) or not history or any(not isinstance(x, dict) for x in history):
        return None
    if history[-1].get("role") != "user":
        return None
    current = reasoning["effort"]
    for index, item in enumerate(history):
        if item.get("type") == "configuration_update":
            if index and history[index - 1].get("type") == "configuration_update":
                return None
            update = item.get("reasoning")
            if not isinstance(update, dict) or update.get("effort") not in _EFFORTS:
                return None
            current = update["effort"]
    if current == target:
        return dict(request, input=list(history))
    if len(history) > 1 and history[-2].get("type") == "configuration_update":
        return None
    marker = {"type": "configuration_update", "reasoning": {"effort": target}}
    return dict(request, input=history[:-1] + [marker, history[-1]])
