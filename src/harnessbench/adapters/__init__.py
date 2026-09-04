"""Adapter registry for AI coding harnesses."""

from typing import Dict, List, Type
from harnessbench.adapters.base import BaseHarnessAdapter
from harnessbench.adapters.aider import AiderAdapter
from harnessbench.adapters.claude_code import ClaudeCodeAdapter
from harnessbench.adapters.codeless import CodelessAdapter
from harnessbench.adapters.mock import MockAdapter

ADAPTER_REGISTRY: Dict[str, Type[BaseHarnessAdapter]] = {
    "aider": AiderAdapter,
    "claude": ClaudeCodeAdapter,
    "claude_code": ClaudeCodeAdapter,
    "codeless": CodelessAdapter,
    "mock": MockAdapter,
}


def get_adapter(name: str, **kwargs) -> BaseHarnessAdapter:
    """Retrieve an instantiated harness adapter by name."""
    norm_name = name.strip().lower()
    adapter_cls = ADAPTER_REGISTRY.get(norm_name)
    if not adapter_cls:
        valid = ", ".join(sorted(ADAPTER_REGISTRY.keys()))
        raise ValueError(f"Unknown harness adapter: '{name}'. Available: {valid}")
    return adapter_cls(**kwargs)


def list_adapters() -> List[str]:
    """List all registered adapter names."""
    return sorted(list(set(ADAPTER_REGISTRY.keys())))
