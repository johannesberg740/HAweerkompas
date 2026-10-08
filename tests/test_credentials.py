"""Regression: optional API credentials must not be required for initial setup."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "neerslagkompas"


def test_api_sources_are_conditional_on_keys():
    source = (ROOT / "__init__.py").read_text()
    module = ast.parse(source)
    tests = [
        ast.unparse(node.test)
        for node in ast.walk(module)
        if isinstance(node, ast.If)
    ]
    assert "settings.get(CONF_KNMI_KEY)" in tests
    assert "settings.get(CONF_WEERLIVE_KEY)" in tests


def test_api_credential_fields_are_optional_and_password_masked():
    flow = (ROOT / "config_flow.py").read_text()
    assert "vol.Optional(CONF_KNMI_KEY): password" in flow
    assert "vol.Optional(CONF_WEERLIVE_KEY): password" in flow
    assert "selector.TextSelectorType.PASSWORD" in flow
