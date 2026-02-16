import re
from textual.app import App, ComposeResult
from textual.widgets import Footer, DirectoryTree, TextArea, Static
from textual.containers import Horizontal, Vertical
from textual import work
from pathlib import Path
from typing import Iterable
from codesensei.scanner import get_file_info

BINARY_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
    '.pdf', '.zip', '.tar', '.gz', '.rar', '.7z',
    '.exe', '.dll', '.so', '.dylib', '.bin',
    '.mp3', '.mp4', '.wav', '.avi', '.mov',
    '.pyc', '.pyd', '.whl',
}

_STRIP_MARKUP = re.compile(r'\[/?[^\]]*\]')


def _plain(text: str) -> str:
    """Strip Rich markup tags from a string."""
    return _STRIP_MARKUP.sub('', text)


BANNER = (
    " ██████╗ ██████╗ ██████╗ ███████╗    ███████╗███████╗███╗   ██╗███████╗███████╗██╗\n"
    "██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔════╝██╔════╝████╗  ██║██╔════╝██╔════╝██║\n"
    "██║     ██║   ██║██║  ██║█████╗      ███████╗█████╗  ██╔██╗ ██║███████╗█████╗  ██║\n"
    "██║     ██║   ██║██║  ██║██╔══╝      ╚════██║██╔══╝  ██║╚██╗██║╚════██║██╔══╝  ██║\n"
    "╚██████╗╚██████╔╝██████╔╝███████╗    ███████║███████╗██║ ╚████║███████║███████╗██║\n"
    " ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝\n"
    "  ──────────────────[ AI-Powered Code Analysis  •  v1.0 ]──────────────────"
)


class FilteredDirectoryTree(DirectoryTree):

    IGNORE = {'.venv', 'venv', '__pycache__', '.git', 'node_modules',
              'env', '.env', 'dist', 'build', '.pytest_cache'}

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if path.name not in self.IGNORE]


class CodeSenseiApp(App):
    """CodeSensei - AI-Powered Development Assistant"""

    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        ("d", "devil", "Devil Mode"),
        ("l", "learn", "Learn Mode"),
        ("r", "review", "Review Mode"),
        ("c", "resolve_conflicts", "Conflicts"),
        ("g", "git_review", "Git Review"),
        ("b", "blueprint", "Blueprint"),
        ("escape", "back", "Back"),
        ("question_mark", "help_screen", "Help"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    #banner {
        background: #0d1117;
        color: #00ff41;
        text-style: bold;
        content-align: center middle;
        height: 9;
        border-bottom: solid #00ff41;
        padding: 0 2;
    }

    Footer {
        background: #0d1117;
        color: #58a6ff;
    }

    FooterKey {
        background: #161b22;
        color: #c9d1d9;
    }

    #left-panel {
        width: 30%;
        border: solid #30363d;
        background: #0d1117;
        color: #c9d1d9;
    }

    #right-panel {
        width: 70%;
    }

    #code-viewer {
        height: 55%;
        border: solid #30363d;
        background: #0d1117;
    }

    #results {
        height: 45%;
        border: solid #30363d;
        background: #0d1117;
        color: #c9d1d9;
        padding: 1;
    }
    """

    def __init__(self, repo_path: str):
        super().__init__()
        self.repo_path = Path(repo_path).resolve()
        self.current_file_path: Path | None = None
        self.current_file_content: str = ""

    def compose(self) -> ComposeResult:
        yield Static(BANNER, id="banner")
        with Horizontal():
            yield FilteredDirectoryTree(self.repo_path, id="left-panel")
            with Vertical(id="right-panel"):
                yield TextArea("", id="code-viewer", read_only=True)
                yield TextArea("", id="results", read_only=True)
        yield Footer()

    def _set_results(self, *lines: str) -> None:
        """Write plain text to the results panel (strips any Rich markup)."""
        text = '\n'.join(_plain(line) for line in lines)
        self.query_one("#results", TextArea).load_text(text)

    def on_mount(self) -> None:
        self._set_results(
            "> CodeSensei v1.0 initialized...",
            "> System online. AI engine ready.",
            "> Awaiting target... select a file to begin.",
            "",
            "  D = Devil Mode    L = Learn Mode    R = Review Mode",
            "  C = Conflict Resolution    G = Git Review",
            "  B = Blueprint Mode",
        )

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        fp = event.path
        self.current_file_path = fp
        viewer = self.query_one("#code-viewer", TextArea)

        # Binary file check
        if fp.suffix.lower() in BINARY_EXTENSIONS:
            self.current_file_content = ""
            viewer.load_text(f"[Binary file: {fp.name}]")
            self._set_results(f"{fp.name}  (binary — cannot analyze)")
            return

        # Read file content
        try:
            content = fp.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            self._set_results(f"Error reading file: {e}")
            return

        self.current_file_content = content
        viewer.load_text(content)

        info = get_file_info(fp)
        if info:
            line_count = len(content.splitlines())
            self._set_results(
                f"File:  {info['name']}",
                f"Size:  {info['size_display']}  •  {line_count} lines",
                f"Path:  {info['path']}",
                "",
                "Press D = Devil Mode  L = Learn Mode  R = Review Mode",
                "      C = Conflict Resolution  G = Git Review",
                "      B = Blueprint",
            )

    # ── Mode Actions ──────────────────────────────────────────────────────────

    def action_devil(self) -> None:
        if not self.current_file_path:
            self._set_results("Select a file first using the file tree.")
            return
        if not self.current_file_content.strip():
            self._set_results("File is empty — nothing to analyze.")
            return

        line_count = len(self.current_file_content.splitlines())
        lines = [f"🔥 Devil Mode — scanning {self.current_file_path.name}"]
        if line_count > 800:
            lines.append(f"⚠ Large file ({line_count} lines) — applying smart truncation...")
        lines.append("Analyzing...")
        self._set_results(*lines)
        self._run_devil()

    def action_learn(self) -> None:
        if not self.current_file_path:
            self._set_results("Select a file first using the file tree.")
            return
        if not self.current_file_content.strip():
            self._set_results("File is empty — nothing to analyze.")
            return

        line_count = len(self.current_file_content.splitlines())
        lines = [f"🎓 Learn Mode — explaining {self.current_file_path.name}"]
        if line_count > 800:
            lines.append(f"⚠ Large file ({line_count} lines) — applying smart truncation...")
        lines.append("Analyzing...")
        self._set_results(*lines)
        self._run_learn()

    def action_review(self) -> None:
        if not self.current_file_path:
            self._set_results("Select a file first using the file tree.")
            return
        if not self.current_file_content.strip():
            self._set_results("File is empty — nothing to analyze.")
            return

        line_count = len(self.current_file_content.splitlines())
        lines = [f"🔍 Review Mode — reviewing {self.current_file_path.name}"]
        if line_count > 800:
            lines.append(f"⚠ Large file ({line_count} lines) — applying smart truncation...")
        lines.append("Analyzing...")
        self._set_results(*lines)
        self._run_review()

    def action_git_review(self) -> None:
        if not self.current_file_path:
            self._set_results("Select a file first using the file tree.")
            return

        from codesensei.scanner import get_staged_diff_for_file
        diff_data = get_staged_diff_for_file(str(self.repo_path), str(self.current_file_path))

        if not diff_data['is_git_repo']:
            self._set_results("⚠ Not a git repository.", "Run: git init")
            return
        if diff_data.get('error'):
            self._set_results(f"Error: {diff_data['error']}")
            return
        if not diff_data['has_changes']:
            self._set_results(
                f"⚠ {self.current_file_path.name} is not staged.",
                "",
                f"To stage it, run:  git add {self.current_file_path.name}",
                "Then press G again.",
            )
            return

        self._set_results(
            f"⚙ Git Review — reviewing staged diff of {self.current_file_path.name}",
            "Analyzing...",
        )
        self._run_git_review()

    def action_resolve_conflicts(self) -> None:
        if not self.current_file_path:
            self._set_results("Select a file first using the file tree.")
            return
        if not self.current_file_content.strip():
            self._set_results("File is empty — nothing to analyze.")
            return

        from codesensei.scanner import has_merge_conflicts
        if not has_merge_conflicts(self.current_file_content):
            self._set_results(
                "No merge conflicts found in this file.",
                "Conflict markers (<<<<<<< HEAD) not detected.",
            )
            return

        self._set_results(
            f"⚡ Conflict Resolution — analyzing {self.current_file_path.name}",
            "Analyzing...",
        )
        self._run_resolve_conflicts()

    def action_blueprint(self) -> None:
        from codesensei.scanner import (
            parse_project, format_project_blueprint,
            parse_structure, format_blueprint,
        )

        # ── FILE-LEVEL: a file is open in the viewer ──────────────────────────
        if self.current_file_path and self.current_file_content.strip():
            filename = self.current_file_path.name
            structure = parse_structure(self.current_file_content, filename)
            skeleton_lines = format_blueprint(structure, filename)
            self._set_results(
                f"📐 Blueprint — {filename}",
                "─────────────────────────────────",
                *skeleton_lines,
                "─────────────────────────────────",
                "",
                "💡 Press D to run a security scan on this structure",
                "",
                "Powered by GitHub Copilot",
            )
            return

        # ── PROJECT-LEVEL: no file selected, scan entire project ──────────────
        project_name = self.repo_path.name
        self._set_results(
            f"📐 Blueprint — {project_name} (whole project)",
            "Building class diagram...",
        )
        project = parse_project(str(self.repo_path))

        if project['total_files'] == 0:
            self._set_results(
                f"📐 Blueprint — {project_name}",
                "No supported source files found in this project.",
                "",
                "💡 Select a file first, then press B for a file-level blueprint.",
            )
            return

        skeleton_lines = format_project_blueprint(project, project_name)
        self._set_results(
            f"📐 Blueprint — {project_name} (whole project)",
            "─────────────────────────────────",
            *skeleton_lines,
            "─────────────────────────────────",
            "",
            "💡 Press D to run a security scan on this structure",
            "",
            "Powered by GitHub Copilot",
        )

    def action_back(self) -> None:
        self.workers.cancel_all()
        viewer = self.query_one("#code-viewer", TextArea)

        if self.current_file_path and self.current_file_content:
            viewer.load_text(self.current_file_content)
            info = get_file_info(self.current_file_path)
            if info:
                line_count = len(self.current_file_content.splitlines())
                self._set_results(
                    f"File:  {info['name']}",
                    f"Size:  {info['size_display']}  •  {line_count} lines",
                    f"Path:  {info['path']}",
                    "",
                    "Press D = Devil Mode  L = Learn Mode  R = Review Mode",
                    "      C = Conflict Resolution  G = Git Review",
                    "      B = Blueprint",
                )
        else:
            viewer.load_text("")
            self._set_results(
                "> CodeSensei ready. Select a file to begin.",
                "",
                "  D = Devil Mode    L = Learn Mode    R = Review Mode",
                "  C = Conflict Resolution    G = Git Review",
                "  B = Blueprint Mode",
            )

    def action_help_screen(self) -> None:
        self._set_results(
            "━━━━━━ CodeSensei Help ━━━━━━",
            "",
            "Keyboard Shortcuts:",
            "  D  Devil Mode   — hostile security scan",
            "  L  Learn Mode   — educational explanation",
            "  R  Review Mode  — senior developer code review",
            "  C  Conflicts    — resolve git merge conflicts",
            "  G  Git Review   — review staged git diff (pre-commit)",
            "  B  Blueprint    — class structure diagram + architectural analysis",
            "  ?  Help         — show this screen",
            "  Q  Quit         — exit CodeSensei",
            "  Esc             — cancel / go back",
            "",
            "Navigation:",
            "  Arrow keys — navigate file tree",
            "  Enter      — select file",
            "",
            "Results panel:",
            "  Click and drag to select text",
            "  Ctrl+A to select all, Ctrl+C to copy",
            "",
            "About:",
            "  CodeSensei — AI-Powered Code Analysis",
            "  Built for the GitHub Copilot CLI Challenge",
        )

    # ── Background Workers ────────────────────────────────────────────────────

    @work(thread=True, exclusive=True)
    def _run_devil(self) -> None:
        from codesensei.copilot import devil_analyze
        fp = self.current_file_path
        if fp is None:
            return
        result = devil_analyze(self.current_file_content, fp.name)
        self.call_from_thread(self._show_result, result, "devil")

    @work(thread=True, exclusive=True)
    def _run_learn(self) -> None:
        from codesensei.copilot import summarize_file
        fp = self.current_file_path
        if fp is None:
            return
        result = summarize_file(self.current_file_content, fp.name)
        self.call_from_thread(self._show_result, result, "learn")

    @work(thread=True, exclusive=True)
    def _run_review(self) -> None:
        from codesensei.copilot import review_file
        fp = self.current_file_path
        if fp is None:
            return
        result = review_file(self.current_file_content, fp.name)
        self.call_from_thread(self._show_result, result, "review")

    @work(thread=True, exclusive=True)
    def _run_git_review(self) -> None:
        from codesensei.copilot import review_diff
        from codesensei.scanner import get_staged_diff_for_file
        fp = self.current_file_path
        if fp is None:
            return
        diff_data = get_staged_diff_for_file(str(self.repo_path), str(fp))
        if not diff_data['has_changes']:
            self.call_from_thread(self._set_results, f"⚠ {fp.name} is not staged.")
            return
        result = review_diff(diff_data['diff'])
        result['reviewed_file'] = fp.name
        self.call_from_thread(self._show_result, result, "git_review")

    @work(thread=True, exclusive=True)
    def _run_resolve_conflicts(self) -> None:
        from codesensei.copilot import resolve_conflicts
        fp = self.current_file_path
        if fp is None:
            return
        result = resolve_conflicts(self.current_file_content, fp.name)
        self.call_from_thread(self._show_result, result, "conflict")

    # ── Display Helpers ───────────────────────────────────────────────────────

    def _show_result(self, result: dict, mode: str) -> None:
        mode_headers = {
            "devil":      "🔥 CodeSensei — Devil Mode",
            "learn":      "🎓 CodeSensei — Learning Mode",
            "review":     "🔍 CodeSensei — Review Mode",
            "conflict":   "⚡ CodeSensei — Conflict Resolution",
            "git_review": "⚙ CodeSensei — Git Review",
            "blueprint":  "📐 CodeSensei — Blueprint Mode",
        }
        mode_tips = {
            "devil":      "💡 Press R for a full code review",
            "learn":      "💡 Press D for security analysis",
            "review":     "💡 Press D for a hostile security scan",
            "conflict":   "💡 Press D for security analysis of resolved code",
            "git_review": "💡 Press D for a full security scan of the file",
            "blueprint":  "💡 Press D to run a security scan on this structure",
        }

        lines = [mode_headers.get(mode, "CodeSensei")]

        if mode == "git_review" and result.get('reviewed_file'):
            lines.append(f"Staged diff of: {result['reviewed_file']}")

        if mode == "conflict" and result.get('conflict_count') is not None:
            lines.append(f"Found {result['conflict_count']} conflict(s) in file")

        trunc = result.get('truncation', {})
        if trunc.get('was_truncated') or trunc.get('comments_removed', 0) > 0:
            orig = trunc.get('original_lines', '?')
            removed = trunc.get('comments_removed', 0)
            lines.append(f"⚠ File truncated (original: {orig} lines)")
            if removed > 0:
                lines.append(f"  → {removed} comment-only lines removed to fit more code")
            if trunc.get('was_truncated'):
                lines.append("  → Hard cut at 800 lines — bottom of file not analyzed")
            lines.append("─────────────────────────────────")

        if result.get('success'):
            elapsed = result['elapsed_ms'] / 1000
            # Blueprint: skip command line (prompt is too large to be meaningful)
            if mode != "blueprint":
                cmd_display = result['command']
                if len(cmd_display) > 80:
                    cmd_display = cmd_display[:77] + "..."
                lines.append(f"Command: {cmd_display}")
            lines.append(f"⏱ Response: {elapsed:.1f}s")
            lines.append("─────────────────────────────────")
            lines.append(result['response'])
            lines.append("─────────────────────────────────")
            if result.get('stats'):
                lines.append(result['stats'])
        else:
            error = result.get('error', 'Unknown error')
            err_lower = error.lower()
            if '402' in error or 'quota' in err_lower or 'no quota' in err_lower:
                lines += [
                    "⛔ GitHub Copilot quota exceeded (402)",
                    "",
                    "Your Copilot usage limit has been reached.",
                    "Fix:",
                    "  1. Go to: github.com → Settings → Copilot",
                    "  2. Check your plan / subscribe ($10/month)",
                    "  3. Students: education.github.com (free)",
                    "  Run: gh auth status   to check your account",
                ]
            elif '401' in error or 'unauthorized' in err_lower or 'unauthenticated' in err_lower:
                lines += [
                    "⛔ Not authenticated with GitHub Copilot",
                    "Fix: gh auth login",
                ]
            elif 'not found' in err_lower or 'filenotfound' in err_lower or 'no such file' in err_lower:
                lines += [
                    "⛔ GitHub Copilot CLI not found",
                    "Fix: gh extension install github/gh-copilot",
                ]
            elif 'timed out' in err_lower or 'timeout' in err_lower:
                lines += [
                    f"⏱ {error}",
                    "Try selecting a smaller file or run again.",
                ]
            else:
                lines.append(f"Error: {error}")

        lines += ["", mode_tips.get(mode, ""), "", "Powered by GitHub Copilot"]
        self.query_one("#results", TextArea).load_text('\n'.join(lines))


def run_app(path: str = "."):
    app = CodeSenseiApp(path)
    app.run()
