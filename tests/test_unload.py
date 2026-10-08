"""Regression tests for Home Assistant 2026.10 config entry unload contract."""
from pathlib import Path
import ast
import inspect
import sys
import types
from unittest.mock import AsyncMock
import asyncio

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "neerslagkompas" / "__init__.py"


def test_unload_does_not_call_config_entry_async_unload():
    """Home Assistant itself processes callbacks after integration unload returns."""
    module = ast.parse(ROOT.read_text())
    function = next(
        node for node in module.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_unload_entry"
    )
    calls = [
        node for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "async_unload"
    ]
    assert not calls, "Integration must not unload its own config entry"


def test_unload_returns_platform_result():
    module = ast.parse(ROOT.read_text())
    fn = next(node for node in module.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_unload_entry")
    assert len(fn.body) == 2  # docstring and return
    assert isinstance(fn.body[-1], ast.Return)
    assert isinstance(fn.body[-1].value, ast.Await)
