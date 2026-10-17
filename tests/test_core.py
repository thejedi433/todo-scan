"""Tests for todo-scan core functionality."""

import pytest
from pathlib import Path
import tempfile
import os

from todo_scan.core import (
    TodoItem,
    scan_file,
    scan_directory,
    group_by_tag,
    format_summary,
    format_detailed,
    DEFAULT_EXTENSIONS
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestTodoItem:
    def test_str_with_message(self):
        item = TodoItem(file=Path("test.py"), line=10, tag="TODO", message="Fix this")
        assert str(item) == "test.py:10: TODO Fix this"
    
    def test_str_without_message(self):
        item = TodoItem(file=Path("test.py"), line=10, tag="FIXME", message="")
        assert str(item) == "test.py:10: FIXME "


class TestScanFile:
    def test_scan_file_with_todos(self, temp_dir):
        test_file = temp_dir / "test.py"
        test_file.write_text("""
# TODO: implement this
def foo():
    pass  # FIXME: broken
# HACK: temporary workaround
# Normal comment
# XXX: needs review
""")
        
        items = list(scan_file(test_file))
        
        assert len(items) == 4
        assert items[0].tag == "TODO"
        assert items[0].message == "implement this"
        assert items[0].line == 2
        
        assert items[1].tag == "FIXME"
        assert items[1].message == "broken"
        assert items[1].line == 4
        
        assert items[2].tag == "HACK"
        assert items[2].message == "temporary workaround"
        assert items[2].line == 5
        
        assert items[3].tag == "XXX"
        assert items[3].message == "needs review"
        assert items[3].line == 7
    
    def test_scan_file_no_todos(self, temp_dir):
        test_file = temp_dir / "test.py"
        test_file.write_text("# Normal comment\ndef foo():\n    pass\n")
        
        items = list(scan_file(test_file))
        assert len(items) == 0
    
    def test_scan_file_case_insensitive(self, temp_dir):
        test_file = temp_dir / "test.py"
        test_file.write_text("# todo: lowercase\n# Todo: mixed\n# TODO: uppercase\n")
        
        items = list(scan_file(test_file))
        assert len(items) == 3
        assert all(item.tag == "TODO" for item in items)
    
    def test_scan_file_wrong_extension(self, temp_dir):
        test_file = temp_dir / "test.xyz"
        test_file.write_text("# TODO: test\n")
        
        items = list(scan_file(test_file, extensions={'.py'}))
        assert len(items) == 0
    
    def test_scan_file_no_extension_filter(self, temp_dir):
        test_file = temp_dir / "test.xyz"
        test_file.write_text("# TODO: test\n")
        
        items = list(scan_file(test_file, extensions=None))
        assert len(items) == 1
    
    def test_scan_file_nonexistent(self, temp_dir):
        test_file = temp_dir / "nonexistent.py"
        items = list(scan_file(test_file))
        assert len(items) == 0
    
    def test_scan_file_empty(self, temp_dir):
        test_file = temp_dir / "empty.py"
        test_file.write_text("")
        items = list(scan_file(test_file))
        assert len(items) == 0
    
    def test_scan_file_with_colon_separator(self, temp_dir):
        test_file = temp_dir / "test.py"
        test_file.write_text("# TODO: with colon\n# FIXME without colon\n")
        
        items = list(scan_file(test_file))
        assert len(items) == 2
        assert items[0].message == "with colon"
        assert items[1].message == "without colon"


class TestScanDirectory:
    def test_scan_directory_basic(self, temp_dir):
        (temp_dir / "file1.py").write_text("# TODO: one\n")
        (temp_dir / "file2.py").write_text("# FIXME: two\n")
        
        items = list(scan_directory(temp_dir))
        assert len(items) == 2
    
    def test_scan_directory_recursive(self, temp_dir):
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (temp_dir / "file1.py").write_text("# TODO: one\n")
        (subdir / "file2.py").write_text("# FIXME: two\n")
        
        items = list(scan_directory(temp_dir))
        assert len(items) == 2
    
    def test_scan_directory_exclude_git(self, temp_dir):
        git_dir = temp_dir / ".git"
        git_dir.mkdir()
        (git_dir / "file.py").write_text("# TODO: git\n")
        (temp_dir / "file.py").write_text("# TODO: normal\n")
        
        items = list(scan_directory(temp_dir))
        assert len(items) == 1
        assert "normal" in items[0].message
    
    def test_scan_directory_exclude_node_modules(self, temp_dir):
        node_dir = temp_dir / "node_modules"
        node_dir.mkdir()
        (node_dir / "file.py").write_text("# TODO: node\n")
        (temp_dir / "file.py").write_text("# TODO: normal\n")
        
        items = list(scan_directory(temp_dir))
        assert len(items) == 1
    
    def test_scan_directory_custom_extensions(self, temp_dir):
        (temp_dir / "file.py").write_text("# TODO: python\n")
        (temp_dir / "file.js").write_text("# TODO: javascript\n")
        
        items = list(scan_directory(temp_dir, extensions={'.js'}))
        assert len(items) == 1
        assert "javascript" in items[0].message
    
    def test_scan_directory_custom_excludes(self, temp_dir):
        custom_dir = temp_dir / "custom_exclude"
        custom_dir.mkdir()
        (custom_dir / "file.py").write_text("# TODO: custom\n")
        (temp_dir / "file.py").write_text("# TODO: normal\n")
        
        items = list(scan_directory(temp_dir, exclude_dirs={'custom_exclude'}))
        assert len(items) == 1
    
    def test_scan_directory_empty(self, temp_dir):
        items = list(scan_directory(temp_dir))
        assert len(items) == 0


class TestGroupByTag:
    def test_group_by_tag_basic(self):
        items = [
            TodoItem(Path("a.py"), 1, "TODO", "msg1"),
            TodoItem(Path("b.py"), 2, "FIXME", "msg2"),
            TodoItem(Path("c.py"), 3, "TODO", "msg3"),
        ]
        
        groups = group_by_tag(items)
        
        assert len(groups) == 2
        assert len(groups["TODO"]) == 2
        assert len(groups["FIXME"]) == 1
    
    def test_group_by_tag_empty(self):
        groups = group_by_tag([])
        assert len(groups) == 0
    
    def test_group_by_tag_single_tag(self):
        items = [
            TodoItem(Path("a.py"), 1, "TODO", "msg1"),
            TodoItem(Path("b.py"), 2, "TODO", "msg2"),
        ]
        
        groups = group_by_tag(items)
        assert len(groups) == 1
        assert len(groups["TODO"]) == 2


class TestFormatSummary:
    def test_format_summary_basic(self):
        items = [
            TodoItem(Path("a.py"), 1, "TODO", "msg1"),
            TodoItem(Path("b.py"), 2, "FIXME", "msg2"),
            TodoItem(Path("c.py"), 3, "TODO", "msg3"),
        ]
        
        output = format_summary(items)
        
        assert "FIXME: 1" in output
        assert "TODO: 2" in output
        assert "Total: 3 TODOs" in output
    
    def test_format_summary_empty(self):
        output = format_summary([])
        assert output == "No TODOs found."
    
    def test_format_summary_single_tag(self):
        items = [
            TodoItem(Path("a.py"), 1, "HACK", "msg1"),
            TodoItem(Path("b.py"), 2, "HACK", "msg2"),
        ]
        
        output = format_summary(items)
        assert "HACK: 2" in output
        assert "Total: 2 TODOs" in output


class TestFormatDetailed:
    def test_format_detailed_basic(self):
        items = [
            TodoItem(Path("b.py"), 5, "FIXME", "broken"),
            TodoItem(Path("a.py"), 10, "TODO", "implement"),
            TodoItem(Path("a.py"), 20, "TODO", "optimize"),
        ]
        
        output = format_detailed(items)
        
        assert "a.py:" in output
        assert "b.py:" in output
        assert "Line 5: [FIXME]: broken" in output
        assert "Line 10: [TODO]: implement" in output
        assert "Line 20: [TODO]: optimize" in output
    
    def test_format_detailed_empty(self):
        output = format_detailed([])
        assert output == "No TODOs found."
    
    def test_format_detailed_sorted_by_line(self):
        items = [
            TodoItem(Path("a.py"), 20, "TODO", "second"),
            TodoItem(Path("a.py"), 10, "TODO", "first"),
        ]
        
        output = format_detailed(items)
        lines = output.split('\n')
        
        # Find the line numbers in output
        line_10_idx = next(i for i, line in enumerate(lines) if "Line 10" in line)
        line_20_idx = next(i for i, line in enumerate(lines) if "Line 20" in line)
        
        assert line_10_idx < line_20_idx
    
    def test_format_detailed_no_message(self):
        items = [TodoItem(Path("a.py"), 1, "TODO", "")]
        output = format_detailed(items)
        assert "Line 1: [TODO]" in output
        assert ":" not in output.split("Line 1: [TODO]")[1] or output.endswith("[TODO]")


class TestDefaultExtensions:
    def test_default_extensions_contains_common_types(self):
        assert '.py' in DEFAULT_EXTENSIONS
        assert '.js' in DEFAULT_EXTENSIONS
        assert '.ts' in DEFAULT_EXTENSIONS
        assert '.java' in DEFAULT_EXTENSIONS
        assert '.md' in DEFAULT_EXTENSIONS
