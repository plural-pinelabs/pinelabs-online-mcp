"""Tests for pkg/toolsets/toolsets.py — Toolset and ToolsetGroup."""

import pytest

from pkg.toolsets.toolsets import Toolset, ToolsetGroup


class _FakeMCP:
    """Stub MCP that records which registrars touched it."""

    def __init__(self) -> None:
        self.registered: list[str] = []


def _make_registrar(label: str):
    def reg(mcp, *_args):
        mcp.registered.append(label)
    return reg


# ---------------------------------------------------------------------------
# Toolset
# ---------------------------------------------------------------------------

class TestToolset:
    def test_init_defaults(self):
        ts = Toolset("payments", "Payment tools")
        assert ts.name == "payments"
        assert ts.description == "Payment tools"
        assert ts.enabled is False
        assert ts.read_only is False

    def test_add_read_and_write_returns_self(self):
        ts = Toolset("x", "x")
        assert ts.add_read_tools(_make_registrar("r1")) is ts
        assert ts.add_write_tools(_make_registrar("w1")) is ts

    def test_register_skipped_when_disabled(self):
        ts = Toolset("x", "x")
        ts.add_read_tools(_make_registrar("r1"))
        ts.add_write_tools(_make_registrar("w1"))
        mcp = _FakeMCP()
        ts.register_tools(mcp, object())
        assert mcp.registered == []

    def test_register_runs_read_and_write_when_enabled(self):
        ts = Toolset("x", "x")
        ts.add_read_tools(_make_registrar("r1"), _make_registrar("r2"))
        ts.add_write_tools(_make_registrar("w1"))
        ts.enabled = True
        mcp = _FakeMCP()
        ts.register_tools(mcp, object())
        assert mcp.registered == ["r1", "r2", "w1"]

    def test_register_skips_writes_in_read_only(self):
        ts = Toolset("x", "x")
        ts.add_read_tools(_make_registrar("r1"))
        ts.add_write_tools(_make_registrar("w1"))
        ts.enabled = True
        ts.read_only = True
        mcp = _FakeMCP()
        ts.register_tools(mcp, object())
        assert mcp.registered == ["r1"]

    def test_register_passes_args_through(self):
        captured = {}

        def reg(mcp, client, extra):
            captured["client"] = client
            captured["extra"] = extra

        ts = Toolset("x", "x")
        ts.add_read_tools(reg)
        ts.enabled = True
        client = object()
        extra = object()
        ts.register_tools(_FakeMCP(), client, extra)
        assert captured["client"] is client
        assert captured["extra"] is extra


# ---------------------------------------------------------------------------
# ToolsetGroup
# ---------------------------------------------------------------------------

class TestToolsetGroup:
    def test_add_toolset_stores_by_name(self):
        group = ToolsetGroup()
        ts = Toolset("a", "a")
        group.add_toolset(ts)
        assert group.toolsets["a"] is ts

    def test_add_toolset_propagates_read_only(self):
        group = ToolsetGroup(read_only=True)
        ts = Toolset("a", "a")
        group.add_toolset(ts)
        assert ts.read_only is True

    def test_enable_toolset_unknown_raises(self):
        group = ToolsetGroup()
        with pytest.raises(ValueError, match="does not exist"):
            group.enable_toolset("missing")

    def test_enable_toolset_marks_enabled(self):
        group = ToolsetGroup()
        ts = Toolset("a", "a")
        group.add_toolset(ts)
        group.enable_toolset("a")
        assert ts.enabled is True

    def test_enable_toolsets_empty_enables_all(self):
        group = ToolsetGroup()
        a = Toolset("a", "a")
        b = Toolset("b", "b")
        group.add_toolset(a)
        group.add_toolset(b)
        group.enable_toolsets([])
        assert a.enabled and b.enabled

    def test_enable_toolsets_subset(self):
        group = ToolsetGroup()
        a = Toolset("a", "a")
        b = Toolset("b", "b")
        group.add_toolset(a)
        group.add_toolset(b)
        group.enable_toolsets(["a"])
        assert a.enabled is True
        assert b.enabled is False

    def test_register_tools_invokes_each_enabled_toolset(self):
        group = ToolsetGroup()
        a = Toolset("a", "a")
        a.add_read_tools(_make_registrar("a-r"))
        b = Toolset("b", "b")
        b.add_read_tools(_make_registrar("b-r"))
        group.add_toolset(a)
        group.add_toolset(b)
        group.enable_toolset("a")  # only enable a

        mcp = _FakeMCP()
        group.register_tools(mcp, object())
        assert mcp.registered == ["a-r"]

    def test_read_only_group_skips_writes_for_all_toolsets(self):
        group = ToolsetGroup(read_only=True)
        a = Toolset("a", "a")
        a.add_read_tools(_make_registrar("a-r"))
        a.add_write_tools(_make_registrar("a-w"))
        group.add_toolset(a)
        group.enable_toolsets([])

        mcp = _FakeMCP()
        group.register_tools(mcp, object())
        assert mcp.registered == ["a-r"]
