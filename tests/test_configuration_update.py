import pytest

from conftest import import_plugin


def test_full_history_update_preserves_baseline_and_prior_markers():
    module = import_plugin("configuration_update")
    history = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "answer"},
        {"type": "configuration_update", "reasoning": {"effort": "high"}},
        {"role": "user", "content": "second"},
        {"role": "assistant", "content": "answer 2"},
        {"role": "user", "content": "third"},
    ]
    request = {"model": "gpt-6-astra", "reasoning": {"effort": "low"}, "input": history}
    result = module.build_full_replay_update(request, "medium")
    assert result["reasoning"] == {"effort": "low"}
    assert result["input"] == history[:-1] + [
        {"type": "configuration_update", "reasoning": {"effort": "medium"}}, history[-1]]
    assert request["input"] == history


def test_replayed_update_is_idempotent():
    module = import_plugin("configuration_update")
    request = {"reasoning": {"effort": "low"}, "input": [{"role": "user", "content": "x"}]}
    updated = module.build_full_replay_update(request, "high")
    assert module.build_full_replay_update(updated, "high") == updated
    assert module.build_full_replay_update(updated, "medium") is None


@pytest.mark.parametrize("changes", [
    {"previous_response_id": "resp_1"},
    {"reasoning": {"effort": "none"}},
    {"reasoning": {"effort": "low", "mode": "pro"}},
    {"input": "text"},
    {"input": [{"role": "assistant", "content": "x"}]},
    {"input": [{"type": "configuration_update", "reasoning": {}}, {"role": "user"}]},
    {"input": [{"type": "configuration_update", "reasoning": {"effort": "high"}},
               {"type": "configuration_update", "reasoning": {"effort": "low"}},
               {"role": "user"}]},
])
def test_refuses_unsafe_replay(changes):
    module = import_plugin("configuration_update")
    request = {"reasoning": {"effort": "low"}, "input": [{"role": "user", "content": "x"}]}
    request.update(changes)
    assert module.build_full_replay_update(request, "high") is None
