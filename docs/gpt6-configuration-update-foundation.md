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

References: https://developers.openai.com/api/docs/guides/reasoning and
https://openrouter.ai/docs/cookbook/evaluate-and-optimize/model-migrations/gpt-6
