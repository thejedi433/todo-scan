"""Core scanning logic for todo-scan."""

import re
from pathlib import Path
from dataclasses import dataclass
from typing import Iterator


@dataclass
class TodoItem:
    """Represents a TODO/FIXME/HACK comment."""
    file: Path
    line: int
    tag: str
    message: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}: {self.tag} {self.message}"


# Patterns to match TODO-style comments
# Matches: TODO:, TODO, FIXME:, FIXME, HACK:, HACK, XXX:, XXX
TODO_PATTERN = re.compile(
    r'#\s*(TODO|FIXME|HACK|XXX)[:\s]*(.*)',
    re.IGNORECASE
)

# Common file extensions to scan
DEFAULT_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
    '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.sh',
    '.bash', '.zsh', '.yml', '.yaml', '.json', '.md', '.txt', '.sql',
    '.html', '.css', '.scss', '.vue', '.svelte'
}


def scan_file(file_path: Path, extensions: set[str] | None = None) -> Iterator[TodoItem]:
    """Scan a single file for TODO comments.
    
    Args:
        file_path: Path to the file to scan
        extensions: Set of extensions to check (None = all)
    
    Yields:
        TodoItem for each TODO found
    """
    if extensions is not None and file_path.suffix not in extensions:
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, start=1):
                match = TODO_PATTERN.search(line)
                if match:
                    tag = match.group(1).upper()
                    message = match.group(2).strip()
                    yield TodoItem(
                        file=file_path,
                        line=line_num,
                        tag=tag,
                        message=message
                    )
    except (OSError, UnicodeDecodeError):
        # Skip files that can't be read
        pass


def scan_directory(
    root: Path,
    extensions: set[str] | None = None,
    exclude_dirs: set[str] | None = None
) -> Iterator[TodoItem]:
    """Scan all files in a directory recursively.
    
    Args:
        root: Root directory to scan
        extensions: Set of file extensions to check (None = DEFAULT_EXTENSIONS)
        exclude_dirs: Directory names to skip (default: common ones)
    
    Yields:
        TodoItem for each TODO found
    """
    exts = extensions if extensions is not None else DEFAULT_EXTENSIONS
    
    default_excludes = {
        '.git', '.venv', 'venv', 'node_modules', '__pycache__',
        '.pytest_cache', '.mypy_cache', '.tox', 'dist', 'build',
        '.eggs', '*.egg-info', '.idea', '.vscode'
    }
    excludes = exclude_dirs if exclude_dirs is not None else default_excludes
    
    for path in root.rglob('*'):
        if path.is_file():
            # Check if any parent directory should be excluded
            should_skip = False
            for part in path.relative_to(root).parts[:-1]:
                if part in excludes or any(part.endswith(ex) for ex in excludes if '*' in ex):
                    should_skip = True
                    break
            
            if not should_skip:
                yield from scan_file(path, exts)


def group_by_tag(items: list[TodoItem]) -> dict[str, list[TodoItem]]:
    """Group TODO items by their tag type.
    
    Args:
        items: List of TodoItem objects
    
    Returns:
        Dictionary mapping tag -> list of items
    """
    groups: dict[str, list[TodoItem]] = {}
    for item in items:
        if item.tag not in groups:
            groups[item.tag] = []
        groups[item.tag].append(item)
    return groups


def format_summary(items: list[TodoItem]) -> str:
    """Format a summary of TODO items by tag.
    
    Args:
        items: List of TodoItem objects
    
    Returns:
        Formatted summary string
    """
    if not items:
        return "No TODOs found."
    
    groups = group_by_tag(items)
    lines = []
    
    for tag in sorted(groups.keys()):
        count = len(groups[tag])
        lines.append(f"{tag}: {count}")
    
    total = sum(len(v) for v in groups.values())
    lines.append(f"\nTotal: {total} TODOs")
    
    return '\n'.join(lines)


def format_detailed(items: list[TodoItem], show_file: bool = True) -> str:
    """Format detailed output of TODO items.
    
    Args:
        items: List of TodoItem objects
        show_file: Whether to show file paths (True) or just line numbers
    
    Returns:
        Formatted detailed string
    """
    if not items:
        return "No TODOs found."
    
    lines = []
    
    # Group by file
    by_file: dict[Path, list[TodoItem]] = {}
    for item in items:
        if item.file not in by_file:
            by_file[item.file] = []
        by_file[item.file].append(item)
    
    for file_path in sorted(by_file.keys()):
        file_items = sorted(by_file[file_path], key=lambda x: x.line)
        lines.append(f"\n{file_path}:")
        
        for item in file_items:
            msg = f": {item.message}" if item.message else ""
            lines.append(f"  Line {item.line}: [{item.tag}]{msg}")
    
    return '\n'.join(lines)
