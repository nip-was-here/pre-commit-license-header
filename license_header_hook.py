#!/usr/bin/env python3
"""
Pre-commit hook for managing license headers in source files.
"""

__version__ = "0.1.0"

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path


class CommentRegistry:
    """Registry for file extension to comment style mappings."""

    DEFAULT_MAPPINGS = {
        # Python
        ".py": {"start": "#", "middle": "#", "end": "#"},
        ".pyx": {"start": "#", "middle": "#", "end": "#"},
        # JavaScript/TypeScript
        ".js": {"start": "/*", "middle": " *", "end": " */"},
        ".ts": {"start": "/*", "middle": " *", "end": " */"},
        ".jsx": {"start": "/*", "middle": " *", "end": " */"},
        ".tsx": {"start": "/*", "middle": " *", "end": " */"},
        # Java/C/C++
        ".java": {"start": "/*", "middle": " *", "end": " */"},
        ".c": {"start": "/*", "middle": " *", "end": " */"},
        ".cpp": {"start": "/*", "middle": " *", "end": " */"},
        ".cc": {"start": "/*", "middle": " *", "end": " */"},
        ".h": {"start": "/*", "middle": " *", "end": " */"},
        ".hpp": {"start": "/*", "middle": " *", "end": " */"},
        # Shell scripts
        ".sh": {"start": "#", "middle": "#", "end": "#"},
        ".bash": {"start": "#", "middle": "#", "end": "#"},
        # Go
        ".go": {"start": "/*", "middle": " *", "end": " */"},
        # Rust
        ".rs": {"start": "/*", "middle": " *", "end": " */"},
        # CSS/SCSS
        ".css": {"start": "/*", "middle": " *", "end": " */"},
        ".scss": {"start": "/*", "middle": " *", "end": " */"},
        # HTML/XML
        ".html": {"start": "<!--", "middle": "  ", "end": "-->"},
        ".xml": {"start": "<!--", "middle": "  ", "end": "-->"},
        # YAML
        ".yml": {"start": "#", "middle": "#", "end": "#"},
        ".yaml": {"start": "#", "middle": "#", "end": "#"},
        # RTL
        ".vhdl": {"start": "/*", "middle": "", "end": "*/"},
        ".vhd": {"start": "/*", "middle": "", "end": "*/"},
        ".v": {"start": "//", "middle": "//", "end": "//"},
        ".sv": {"start": "//", "middle": "//", "end": "//"},
        # MarkDown
        ".md": {"start": "<!--", "middle": "", "end": "-->"},
        # HashiCorp
        ".hcl": {"start": "#", "middle": "#", "end": "#"},
        ".tf": {"start": "#", "middle": "#", "end": "#"},
    }

    def __init__(self, custom_mappings: dict | None = None):
        self.mappings = self.DEFAULT_MAPPINGS.copy()
        if custom_mappings:
            self.mappings.update(custom_mappings)

    def get_comment_style(self, file_path: str) -> dict[str, str] | None:
        """Get comment style for a file based on its extension."""
        ext = Path(file_path).suffix.lower()
        return self.mappings.get(ext)


class LicenseHeaderManager:
    """Manages license headers in source files."""

    def __init__(
        self,
        template_file: str,
        copyright_holder: str,
        comment_registry: CommentRegistry,
    ):
        self.template_file = template_file
        self.copyright_holder = copyright_holder
        self.comment_registry = comment_registry
        self.current_year = datetime.now().year

    def load_template(self) -> str:
        """Load the license header template."""
        try:
            with open(self.template_file, encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Template file not found: {self.template_file}"
            ) from e

    def format_template(self, template: str) -> str:
        """Format template with current year and copyright holder."""
        return template.format(
            year=self.current_year, copyright_holder=self.copyright_holder
        )

    def create_header_comment(self, content: str, comment_style: dict[str, str]) -> str:
        """Create a commented header from content."""
        lines = content.split("\n")

        if comment_style["start"] == comment_style["middle"] == comment_style["end"]:
            # Single-line comment style (e.g., # for Python)
            return "\n".join(
                f"{comment_style['start']} {line}".rstrip() for line in lines
            )
        else:
            # Multi-line comment style (e.g., /* */ for C/Java)
            result = [comment_style["start"]]
            for line in lines:
                result.append(f"{comment_style['middle']} {line}".rstrip())
            result.append(comment_style["end"])
            return "\n".join(result)

    def extract_existing_header(
        self, file_content: str, comment_style: dict[str, str]
    ) -> str | None:
        """Extract existing license header from file content."""
        lines = file_content.split("\n")

        # Skip shebang if present
        start_idx = 0
        if lines and lines[0].startswith("#!"):
            start_idx = 1

        # Skip empty lines
        while start_idx < len(lines) and not lines[start_idx].strip():
            start_idx += 1

        if start_idx >= len(lines):
            return None

        # Check if we have a comment block starting
        first_line = lines[start_idx].strip()

        if comment_style["start"] == comment_style["middle"]:
            # Single-line comments
            if not first_line.startswith(comment_style["start"]):
                return None

            header_lines = []
            for i in range(start_idx, len(lines)):
                line = lines[i].strip()
                if line.startswith(comment_style["start"]):
                    header_lines.append(line)
                elif not line:  # Empty line
                    continue
                else:
                    break

            return "\n".join(header_lines) if header_lines else None

        else:
            # Multi-line comments
            if not first_line.startswith(comment_style["start"]):
                return None

            header_lines = []

            for i in range(start_idx, len(lines)):
                line = lines[i].strip()
                header_lines.append(lines[i])

                if comment_style["end"] in line:
                    break

            return "\n".join(header_lines) if header_lines else None

    def _extract_header_content(
        self, header: str, comment_style: dict[str, str]
    ) -> str:
        """Extract the actual content from a commented header."""
        lines = header.split("\n")
        content_lines = []

        if comment_style["start"] == comment_style["middle"]:
            # Single-line comments - remove comment prefix
            for line in lines:
                stripped = line.strip()
                if stripped.startswith(comment_style["start"]):
                    content = stripped[len(comment_style["start"]):].strip()
                    content_lines.append(content)
        else:
            # Multi-line comments - remove comment markers
            for i, line in enumerate(lines):
                stripped = line.strip()
                if i == 0 and stripped.startswith(comment_style["start"]):
                    # First line with start marker
                    content = stripped[len(comment_style["start"]):].strip()
                    if content:
                        content_lines.append(content)
                elif stripped.endswith(comment_style["end"]):
                    # Last line with end marker
                    content = stripped[: -len(comment_style["end"])].strip()
                    if content.startswith(comment_style["middle"].strip()):
                        content = content[
                            len(comment_style["middle"].strip()):
                        ].strip()
                    if content:
                        content_lines.append(content)
                    break
                elif stripped.startswith(comment_style["middle"].strip()):
                    # Middle line
                    content = stripped[len(
                        comment_style["middle"].strip()):].strip()
                    content_lines.append(content)

        return "\n".join(content_lines)

    def remove_existing_header(
        self, file_content: str, comment_style: dict[str, str]
    ) -> str:
        """Remove existing license header from file content."""
        # First, check if there's actually a header to remove
        existing_header = self.extract_existing_header(
            file_content, comment_style)
        if not existing_header:
            return file_content

        lines = file_content.split("\n")
        header_lines = existing_header.split("\n")

        # Preserve shebang
        start_idx = 0
        preserved_lines = []
        if lines and lines[0].startswith("#!"):
            preserved_lines.append(lines[0])
            start_idx = 1

        # Skip empty lines before header
        while start_idx < len(lines) and not lines[start_idx].strip():
            start_idx += 1

        if start_idx >= len(lines):
            return file_content

        # Remove the exact header lines that were detected
        if comment_style["start"] == comment_style["middle"]:
            # Single-line comments - remove exact matching header lines
            header_end_idx = start_idx
            for expected_line in header_lines:
                if (
                    header_end_idx < len(lines)
                    and lines[header_end_idx].strip() == expected_line.strip()
                ):
                    header_end_idx += 1
                else:
                    break

            # Skip empty lines after header
            while header_end_idx < len(lines) and not lines[header_end_idx].strip():
                header_end_idx += 1

            start_idx = header_end_idx
        else:
            # Multi-line comments - find the end of the specific header block
            first_line = lines[start_idx].strip()
            if first_line.startswith(comment_style["start"]):
                while start_idx < len(lines):
                    line = lines[start_idx]
                    start_idx += 1
                    if comment_style["end"] in line:
                        break

                # Skip empty lines after header
                while start_idx < len(lines) and not lines[start_idx].strip():
                    start_idx += 1

        # Return preserved lines + remaining content
        remaining_lines = lines[start_idx:] if start_idx < len(lines) else []
        return "\n".join(preserved_lines + remaining_lines)

    def process_file(self, file_path: str) -> bool:
        """Process a single file to add/update license header."""
        comment_style = self.comment_registry.get_comment_style(file_path)
        if not comment_style:
            print(f"Skipping {file_path}: No comment style registered")
            return False

        try:
            with open(file_path, encoding="utf-8") as f:
                original_content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return False

        # Load and format template
        template = self.load_template()
        formatted_template = self.format_template(template)
        new_header = self.create_header_comment(
            formatted_template, comment_style)

        # TODO: Add optimization to check if existing header is already correct

        # Remove existing header if present
        content_without_header = self.remove_existing_header(
            original_content, comment_style
        )

        # Create new content with header
        # Check if original content starts with shebang
        lines = original_content.split("\n")
        if lines and lines[0].startswith("#!"):
            # Preserve shebang at the top
            shebang = lines[0]
            remaining_content = content_without_header
            if remaining_content.startswith(shebang):
                remaining_content = remaining_content[len(
                    shebang):].lstrip("\n")

            remaining_content = remaining_content.lstrip("\n")
            if remaining_content:
                new_content = shebang + "\n" + new_header + "\n" + remaining_content
            else:
                new_content = shebang + "\n" + new_header + "\n"
        else:
            remaining_content = content_without_header.lstrip("\n")
            if remaining_content:
                new_content = new_header + "\n" + remaining_content
            else:
                new_content = new_header + "\n"

        # Write back if changed
        if new_content != original_content:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated license header in {file_path}")
                return True
            except Exception as e:
                print(f"Error writing {file_path}: {e}")
                return False

        return False


def should_process_file(
    file_path: str, include_patterns: list[str], exclude_patterns: list[str]
) -> bool:
    """Check if file should be processed based on include/exclude patterns."""
    path = Path(file_path)

    # Check exclude patterns first
    for pattern in exclude_patterns:
        if path.match(pattern):
            return False

    # If no include patterns, process all (except excluded)
    if not include_patterns:
        return True

    # Check include patterns
    for pattern in include_patterns:
        if path.match(pattern):
            return True

    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pre-commit hook for license headers")
    parser.add_argument("files", nargs="*", help="Files to process")
    parser.add_argument(
        "--template", "-t", required=True, help="License header template file"
    )
    parser.add_argument(
        "--copyright-holder", "-c", required=True, help="Copyright holder name"
    )
    parser.add_argument(
        "--include",
        "-i",
        action="append",
        default=[],
        help="File patterns to include (can be used multiple times)",
    )
    parser.add_argument(
        "--exclude",
        "-e",
        action="append",
        default=[],
        help="File patterns to exclude (can be used multiple times)",
    )

    args = parser.parse_args()

    # Initialize components
    comment_registry = CommentRegistry()
    header_manager = LicenseHeaderManager(
        args.template, args.copyright_holder, comment_registry
    )

    # Process files
    modified_files = []

    for file_path in args.files:
        if not os.path.isfile(file_path):
            continue

        if not should_process_file(file_path, args.include, args.exclude):
            continue

        if header_manager.process_file(file_path):
            modified_files.append(file_path)

    # Return appropriate exit code
    if modified_files:
        print(f"\nModified {len(modified_files)} files with license headers")
        return 1  # Pre-commit expects 1 when files are modified

    return 0


if __name__ == "__main__":
    sys.exit(main())
