"""Tests for harness adapter interfaces and command construction."""

import pytest
from pathlib import Path
from harnessbench.adapters import get_adapter, list_adapters
from harnessbench.adapters.aider import AiderAdapter
from harnessbench.adapters.claude_code import ClaudeCodeAdapter
from harnessbench.adapters.codeless import CodelessAdapter
from harnessbench.adapters.mock import MockAdapter
from harnessbench.execution.process import scrub_secrets


def test_adapter_registry():
    adapters = list_adapters()
    assert "aider" in adapters
    assert "claude" in adapters
    assert "codeless" in adapters
    assert "mock" in adapters

    with pytest.raises(ValueError, match="Unknown harness adapter"):
        get_adapter("nonexistent_agent")


def test_aider_adapter_initialization(tmp_path: Path):
    adapter = AiderAdapter()
    assert adapter.name == "aider"
    # setup & teardown should be safe no-ops
    adapter.setup(cwd=tmp_path, env={})
    adapter.teardown(cwd=tmp_path)


def test_claude_adapter_initialization(tmp_path: Path):
    adapter = ClaudeCodeAdapter()
    assert adapter.name == "claude_code"
    adapter.setup(cwd=tmp_path, env={})
    adapter.teardown(cwd=tmp_path)


def test_codeless_adapter_initialization(tmp_path: Path):
    adapter = CodelessAdapter()
    assert adapter.name == "codeless"
    adapter.setup(cwd=tmp_path, env={})
    adapter.teardown(cwd=tmp_path)


def test_mock_adapter_behavior(tmp_path: Path):
    # Test successful mock execution
    mock = MockAdapter(behavior="solve", extra_stdout="Done")
    res = mock.run("Fix the bug", cwd=tmp_path, env={})
    assert res.exit_code == 0
    assert "Done" in res.stdout

    # Test failure mode
    failing_mock = MockAdapter(fail=True)
    res_fail = failing_mock.run("Fix bug", cwd=tmp_path, env={})
    assert res_fail.exit_code == 1

    # Test pollution simulation
    polluting_mock = MockAdapter(pollute=True)
    polluting_mock.run("Fix bug", cwd=tmp_path, env={})
    assert (tmp_path / "agent_notes_scratch.md").exists()


def test_scrub_secrets():
    env = {"ANTHROPIC_API_KEY": "sk-ant-api03-abcdef1234567890abcdef"}
    raw_output = "Connected with sk-ant-api03-abcdef1234567890abcdef securely."
    scrubbed = scrub_secrets(raw_output, env)
    assert "sk-ant-api03" not in scrubbed
    assert "REDACTED" in scrubbed
