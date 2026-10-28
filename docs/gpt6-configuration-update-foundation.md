# GPT-6 configuration updates: foundation only

`configuration_update.py` is a deliberately unwired, pure full-replay builder.
It does not change plugin behavior or send configuration updates. The caller
must establish that the provider, model, API, and mode support the item; this
helper is not a capability registry. A synthetic Codex OAuth GPT-6.1-terra
request with an update returned HTTP 200 and a cache hit, but did not establish
that effective reasoning changed. The installed Hermes Codex preflight rejects
the item after middleware, so production integration also needs a host transport
change. OpenRouter Chat Completions has a different wire shape, and
pro/tournament variants do not accept this Responses item.

Production integration must durably store the original request-level baseline
and the complete ordered sequence of updates alongside conversation history,
replay them identically on tool loops and after process restarts, handle request
errors without falsely committing history, and explicitly re-establish the
appropriate update after compaction. It must detect missing or truncated history
and fail safe rather than emit a partial replay. The helper cannot verify history
completeness, route support, persistence, concurrency, or compaction; do not wire
it into middleware until those guarantees and integration tests exist. It only
handles full Responses input lists, not previous_response_id or Chat messages.

## Integration blocker reproduced against Hermes bf0203a794

The isolated host worktree at that revision was tested, not installed. The
network-free `tests/test_configuration_update_host_blocker.py` exercises the
actual adapter and demonstrates two separate failures:

1. `agent/turn_api_request.py` preflights before plugin middleware, but
   `agent/turn_api_call.py` preflights again immediately before dispatch.
   `agent/codex_responses_adapter.py` has no handler for
   `configuration_update`; the second pass raises `ValueError: ... unsupported
   item shape`. Adding a validated handler alone does not solve replay.
2. The builder only modifies the outbound payload; it does not persist it in
   Hermes conversation history. When Hermes reconstructs a later input from the
   transcript, the old marker is missing and the builder places the transition
   at the new user boundary instead. The test checks this concrete discrepancy.

The existing history store is best-effort and its hot-path writes can be
omitted under contention; it is not an authoritative transaction log. Current
post/error hooks only feed route-trial metrics. Hook payloads may be truncated,
so they cannot serve as a complete replay log. A timeout or process failure
around dispatch also leaves acceptance uncertain; success-only commits and
blind rollback are both insufficient without a deterministic recovery protocol.
Native checkpoint pruning and local compression additionally change input
history and require an explicit new baseline/epoch and tested transition rules.

**Not implemented:** No validated durable, concurrency-safe protocol tying each
baseline and ordered marker to canonical conversation history, retries and
compaction has been established. The synthetic HTTP 200 does not prove the
update's effective reasoning level or cache preservation on later replay. For
these reasons the helper remains unwired and the host worktree remains
unchanged; permitting the item alone would give a false impression of a safe
integration. Resolving this requires an explicitly route-gated transport change,
crash-safe persistence and reconciliation, and end-to-end tests covering
restart, retry/ambiguous dispatch, concurrent requests, tool loops, route
changes and both forms of compaction, plus provider-side semantic validation.
The blocker tests deliberately capture current limitations and must be replaced
when a complete integration changes these behaviors.

References: https://developers.openai.com/api/docs/guides/reasoning and
https://openrouter.ai/docs/cookbook/evaluate-and-optimize/model-migrations/gpt-6
