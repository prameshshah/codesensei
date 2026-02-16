"""
CodeSensei preflight checks — runs before the TUI launches.
Verifies Python version, gh CLI, Copilot extension, and auth.
"""
import sys
import subprocess
import os


def _run(cmd, timeout=5):
    """Run a command silently. Returns (returncode, stdout, stderr)."""
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", timeout=timeout, creationflags=flags
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return -1, "", "not found"
    except subprocess.TimeoutExpired:
        return -2, "", "timed out"


def check_python_version():
    if sys.version_info < (3, 10):
        return False, (
            f"Python 3.10+ required. You have {sys.version_info.major}.{sys.version_info.minor}.\n"
            "  Fix: https://www.python.org/downloads/"
        )
    return True, None


def check_gh_installed():
    code, _, _ = _run(["gh", "--version"])
    if code != 0:
        return False, (
            "GitHub CLI (gh) is not installed.\n"
            "  Fix: https://cli.github.com\n"
            "  Windows : winget install --id GitHub.cli\n"
            "  Mac     : brew install gh\n"
            "  Linux   : see https://cli.github.com/manual/installation"
        )
    return True, None


def check_copilot_extension():
    code, _, _ = _run(["gh", "copilot", "--version"])
    if code != 0:
        return False, (
            "GitHub Copilot CLI extension is not installed.\n"
            "  Fix: gh extension install github/gh-copilot"
        )
    return True, None


def check_gh_auth():
    code, _, _ = _run(["gh", "auth", "status"])
    if code != 0:
        return False, (
            "Not authenticated with GitHub.\n"
            "  Fix: gh auth login\n"
            "  SSH / headless server: gh auth login --with-token < token.txt"
        )
    return True, None


def run_preflight() -> bool:
    """
    Run all startup checks. Prints clear errors and returns False if
    any critical check fails so app.py can exit before launching the TUI.

    Checks are run in dependency order — if gh is not installed, the
    Copilot extension and auth checks are skipped to avoid misleading errors.
    """
    errors = []
    warnings = []

    # Step 1: Python version (no dependencies)
    ok, msg = check_python_version()
    if not ok:
        errors.append(("Python version", msg))

    # Step 2: gh CLI (required for all subsequent checks)
    gh_ok, gh_msg = check_gh_installed()
    if not gh_ok:
        errors.append(("GitHub CLI (gh)", gh_msg))
        # gh not found — skip extension and auth checks, they would all fail
        # and would produce misleading duplicate errors
    else:
        # Step 3: Copilot extension (only if gh is present)
        ok, msg = check_copilot_extension()
        if not ok:
            errors.append(("Copilot CLI extension", msg))

        # Step 4: GitHub auth (warn only, not blocking)
        ok, msg = check_gh_auth()
        if not ok:
            warnings.append(("GitHub authentication", msg))

    if errors:
        print("\n" + "=" * 52, file=sys.stderr)
        print("  CodeSensei — Setup Required", file=sys.stderr)
        print("=" * 52, file=sys.stderr)
        for label, msg in errors:
            print(f"\n  [MISSING] {label}", file=sys.stderr)
            print(f"  {msg}", file=sys.stderr)
        print("\n" + "=" * 52, file=sys.stderr)
        print("  Fix the issues above, then run again.", file=sys.stderr)
        print("=" * 52 + "\n", file=sys.stderr)
        return False

    if warnings:
        print("\n" + "-" * 52, file=sys.stderr)
        print("  CodeSensei — Warning", file=sys.stderr)
        print("-" * 52, file=sys.stderr)
        for label, msg in warnings:
            print(f"\n  [WARNING] {label}", file=sys.stderr)
            print(f"  {msg}", file=sys.stderr)
        print("\n  CodeSensei will still launch but AI modes may fail.", file=sys.stderr)
        print("-" * 52 + "\n", file=sys.stderr)

    return True
