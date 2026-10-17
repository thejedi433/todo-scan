"""Tests for todo-scan CLI."""

import pytest
from pathlib import Path
import tempfile
import sys
from io import StringIO

from todo_scan.cli import main as cli_main


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def setup_test_dir(temp_dir):
    """Helper to create test files in temp_dir."""
    def _create(files):
        for name, content in files.items():
            (temp_dir / name).write_text(content)
        return temp_dir
    return _create


class TestCLI:
    def test_summary_default(self, temp_dir, monkeypatch):
        (temp_dir / "test.py").write_text("# TODO: one\n# FIXME: two\n")
        monkeypatch.setattr(sys, 'argv', ['todo-scan', str(temp_dir)])
        monkeypatch.setattr(sys, 'stdout', StringIO())
        
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        
        assert exc_info.value.code == 0
        output = sys.stdout.getvalue()
        assert "TODO: 1" in output
        assert "FIXME: 1" in output
        assert "Total: 2" in output
    
    def test_detailed_flag(self, temp_dir, monkeypatch):
        (temp_dir / "test.py").write_text("# TODO: implement this\n")
        monkeypatch.setattr(sys, 'argv', ['todo-scan', '--detailed', str(temp_dir)])
        monkeypatch.setattr(sys, 'stdout', StringIO())
        
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        
        assert exc_info.value.code == 0
        output = sys.stdout.getvalue()
        assert "test.py:" in output
        assert "[TODO]: implement this" in output
    
    def test_summary_flag(self, temp_dir, monkeypatch):
        (temp_dir / "test.py").write_text("# TODO: one\n")
        monkeypatch.setattr(sys, 'argv', ['todo-scan', '--summary', str(temp_dir)])
        monkeypatch.setattr(sys, 'stdout', StringIO())
        
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        
        assert exc_info.value.code == 0
        output = sys.stdout.getvalue()
        assert "TODO: 1" in output
    
    def test_nonexistent_path(self, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['todo-scan', '/nonexistent/path'])
        monkeypatch.setattr(sys, 'stderr', StringIO())
        
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        
        assert exc_info.value.code == 1
        assert "does not exist" in sys.stderr.getvalue()
    
    def test_file_not_directory(self, temp_dir, monkeypatch):
        test_file = temp_dir / "test.py"
        test_file.write_text("# TODO: test\n")
        monkeypatch.setattr(sys, 'argv', ['todo-scan', str(test_file)])
        monkeypatch.setattr(sys, 'stderr', StringIO())
        
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        
        assert exc_info.value.code == 1
        assert "not a directory" in sys.stderr.getvalue()
    
    def test_extension_filter(self, temp_dir, monkeypatch):
        (temp_dir / "file.py").write_text("# TODO: python\n")
        (temp_dir / "file.js").write_text("# TODO: javascript\n")
        
        monkeypatch.setattr(sys, 'argv', ['todo-scan', '--ext', '.py', str(temp_dir)])
        monkeypatch.setattr(sys, 'stdout', StringIO())
        
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        
        assert exc_info.value.code == 0
        output = sys.stdout.getvalue()
        assert "TODO: 1" in output
        assert "Total: 1" in output
    
    def test_extension_filter_no_dot(self, temp_dir, monkeypatch):
        (temp_dir / "file.py").write_text("# TODO: python\n")
        (temp_dir / "file.js").write_text("# TODO: javascript\n")
        
        monkeypatch.setattr(sys, 'argv', ['todo-scan', '-e', 'py', str(temp_dir)])
        monkeypatch.setattr(sys, 'stdout', StringIO())
        
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        
        assert exc_info.value.code == 0
        assert "Total: 1" in sys.stdout.getvalue()
    
    def test_empty_directory(self, temp_dir, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['todo-scan', str(temp_dir)])
        monkeypatch.setattr(sys, 'stdout', StringIO())
        
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        
        assert exc_info.value.code == 0
        assert "No TODOs found" in sys.stdout.getvalue()
    
    def test_default_path_current_dir(self, temp_dir, monkeypatch):
        (temp_dir / "test.py").write_text("# TODO: test\n")
        monkeypatch.chdir(temp_dir)
        monkeypatch.setattr(sys, 'argv', ['todo-scan'])
        monkeypatch.setattr(sys, 'stdout', StringIO())
        
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        
        assert exc_info.value.code == 0
        assert "TODO: 1" in sys.stdout.getvalue()
    
    def test_exclude_git_directory(self, temp_dir, monkeypatch):
        git_dir = temp_dir / ".git"
        git_dir.mkdir()
        (git_dir / "test.py").write_text("# TODO: in git\n")
        (temp_dir / "test.py").write_text("# TODO: in project\n")
        
        monkeypatch.setattr(sys, 'argv', ['todo-scan', str(temp_dir)])
        monkeypatch.setattr(sys, 'stdout', StringIO())
        
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        
        assert "TODO: 1" in sys.stdout.getvalue()
    
    def test_multiple_extension_filters(self, temp_dir, monkeypatch):
        (temp_dir / "file.py").write_text("# TODO: python\n")
        (temp_dir / "file.js").write_text("# TODO: javascript\n")
        (temp_dir / "file.go").write_text("# TODO: golang\n")
        
        monkeypatch.setattr(sys, 'argv', ['todo-scan', '-e', '.py', '-e', '.js', str(temp_dir)])
        monkeypatch.setattr(sys, 'stdout', StringIO())
        
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        
        assert "Total: 2" in sys.stdout.getvalue()
    
    def test_detailed_multiple_files(self, temp_dir, monkeypatch):
        (temp_dir / "a.py").write_text("# TODO: first\n")
        (temp_dir / "b.py").write_text("# FIXME: second\n")
        
        monkeypatch.setattr(sys, 'argv', ['todo-scan', '--detailed', str(temp_dir)])
        monkeypatch.setattr(sys, 'stdout', StringIO())
        
        with pytest.raises(SystemExit) as exc_info:
            cli_main()
        
        output = sys.stdout.getvalue()
        assert "a.py:" in output
        assert "b.py:" in output
        assert "[TODO]: first" in output
        assert "[FIXME]: second" in output
