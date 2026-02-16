"""
CodeSensei v1.0 — AI-Powered Code Analysis
Powered by GitHub Copilot CLI

Usage:
  python app.py                   # launch on current directory
  python app.py <project-path>    # launch on a specific folder
  python app.py --help            # show help
  python app.py --version         # show version
"""
import sys
import os
from pathlib import Path

HELP_TEXT = """
CodeSensei v1.0 — AI-Powered Code Analysis
Powered by GitHub Copilot CLI

USAGE
  python app.py [project-path]

EXAMPLES
  python app.py                   # current directory
  python app.py demo_project      # relative path
  python app.py /home/user/myapp  # absolute path

MODES  (keyboard shortcuts inside the app)
  D  Devil Mode     — hostile security vulnerability scan
  L  Learn Mode     — educational explanation for any file
  R  Review Mode    — senior developer code review (0–10 score)
  G  Git Review     — AI review of your staged git diff
  C  Conflicts      — resolve git merge conflicts
  B  Blueprint      — full project architecture diagram

NAVIGATION
  Arrow keys / Enter — navigate the file tree
  Esc                — cancel current operation
  ?                  — help screen inside the app
  Q                  — quit

REQUIREMENTS
  Python 3.10+
  GitHub CLI         https://cli.github.com
  Copilot extension  gh extension install github/gh-copilot
  Authentication     gh auth login

TIPS
  SSH / headless server auth:  gh auth login --with-token < token.txt
  Works in any terminal — VS Code, iTerm2, Windows Terminal, PuTTY, SSH
""".strip()


def _set_utf8():
    """Force UTF-8 output so the ASCII art banner renders correctly everywhere."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    # Windows: set PYTHONIOENCODING so subprocesses also use UTF-8
    if os.name == "nt":
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def main():
    _set_utf8()

    args = sys.argv[1:]

    if args and args[0] in ("--version", "-v"):
        print("CodeSensei v1.0")
        sys.exit(0)

    if args and args[0] in ("--help", "-h"):
        print(HELP_TEXT)
        sys.exit(0)

    # Resolve project path
    raw = args[0] if args else "."
    path = Path(raw).resolve()

    if not path.exists():
        print(f"\nError: Path does not exist: {path}", file=sys.stderr)
        print("Usage: python app.py [project-path]\n", file=sys.stderr)
        sys.exit(1)

    if not path.is_dir():
        print(f"\nError: '{path.name}' is a file, not a folder.", file=sys.stderr)
        print("CodeSensei needs a project folder. Example: python app.py my_project/\n", file=sys.stderr)
        sys.exit(1)

    # Run preflight checks before launching the TUI
    from codesensei.preflight import run_preflight
    if not run_preflight():
        sys.exit(1)

    from codesensei.ui import run_app
    run_app(str(path))


if __name__ == "__main__":
    main()
