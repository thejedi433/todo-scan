"""Command-line interface for todo-scan."""

import argparse
import sys
from pathlib import Path

from .core import scan_directory, format_summary, format_detailed


def main():
    """Main entry point for todo-scan CLI."""
    parser = argparse.ArgumentParser(
        description='Scan source files for TODO/FIXME/HACK comments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  todo-scan .                      # Scan current directory
  todo-scan --detailed src/        # Show line numbers and messages
  todo-scan --summary .            # Show counts by tag only
  todo-scan -e .py -e .js src/     # Scan only Python and JS files
        '''
    )
    
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        type=Path,
        help='Directory to scan (default: current directory)'
    )
    
    parser.add_argument(
        '--detailed', '-d',
        action='store_true',
        help='Show file, line number, and message for each TODO'
    )
    
    parser.add_argument(
        '--summary', '-s',
        action='store_true',
        help='Show summary counts by tag (default if neither --detailed nor --summary)'
    )
    
    parser.add_argument(
        '--ext', '-e',
        action='append',
        metavar='EXT',
        help='File extensions to scan (e.g., -e .py -e .js). Default: all common source files'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='%(prog)s 0.1.0'
    )
    
    args = parser.parse_args()
    
    # Validate path
    if not args.path.exists():
        print(f"Error: {args.path} does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not args.path.is_dir():
        print(f"Error: {args.path} is not a directory", file=sys.stderr)
        sys.exit(1)
    
    # Parse extensions
    extensions = None
    if args.ext:
        extensions = set()
        for ext in args.ext:
            if not ext.startswith('.'):
                ext = '.' + ext
            extensions.add(ext)
    
    # Scan
    items = list(scan_directory(args.path, extensions))
    
    # Output
    if args.detailed:
        print(format_detailed(items))
    elif args.summary or not args.detailed:
        print(format_summary(items))
    
    # Exit with count
    sys.exit(0)


if __name__ == '__main__':
    main()
