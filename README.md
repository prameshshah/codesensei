```
 ██████╗ ██████╗ ██████╗ ███████╗    ███████╗███████╗███╗   ██╗███████╗███████╗██╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔════╝██╔════╝████╗  ██║██╔════╝██╔════╝██║
██║     ██║   ██║██║  ██║█████╗      ███████╗█████╗  ██╔██╗ ██║███████╗█████╗  ██║
██║     ██║   ██║██║  ██║██╔══╝      ╚════██║██╔══╝  ██║╚██╗██║╚════██║██╔══╝  ██║
╚██████╗╚██████╔╝██████╔╝███████╗    ███████║███████╗██║ ╚████║███████║███████╗██║
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝
```

<div align="center">

**AI-powered code analysis — security, review, learning, and architecture — all in your terminal.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Textual](https://img.shields.io/badge/Textual-TUI_Framework-7c3aed?style=flat-square)](https://textual.textualize.io/)
[![GitHub Copilot](https://img.shields.io/badge/GitHub_Copilot-CLI-24292f?style=flat-square&logo=github&logoColor=white)](https://docs.github.com/en/copilot/github-copilot-in-the-cli)
[![Platform](https://img.shields.io/badge/Platform-Windows_%7C_macOS_%7C_Linux-lightgrey?style=flat-square)]()
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
[![Challenge](https://img.shields.io/badge/GitHub_Copilot_CLI_Challenge-February_2026-f59e0b?style=flat-square)]()

</div>

---

## The Problem

Every developer has shipped a SQL injection vulnerability they stared at for an hour and never saw. Every team has merged a conflict they didn't fully understand. Every codebase has an architecture diagram that was outdated the week it was drawn.

Security scanners are expensive and noisy. Senior reviewers are busy and async. Architecture diagrams are manual and stale. And your linter has no idea what your code *actually does*.

## The Solution

CodeSensei is a keyboard-driven terminal application that gives every developer — junior or senior — instant access to six expert-level AI analysis modes, powered by GitHub Copilot CLI, without leaving the terminal.

Select a file. Press a key. Get expert output in seconds.

It doesn't replace your editor. It runs alongside it — a second set of expert eyes that never sleeps, never gets interrupted, and never charges by the hour.

---

## Live Preview

```
┌─ CodeSensei v1.0 ─────────────────────────────────────────────────────────────────┐
│                   │  auth.py                            │                          │
│  your-project/    │                                     │  🔥 Devil Mode           │
│  ├── auth.py      │  import sqlite3                     │  ─────────────────────── │
│  ├── models.py    │  import hashlib                     │  CRITICAL: SQL Injection │
│  ├── routes.py    │  import os                          │  Line 21 — username is   │
│  ├── utils.py     │                                     │  inserted directly into  │
│  └── tests/       │  API_KEY = "sk-123..."              │  the query string. Use   │
│      └── ...      │                                     │  parameterised queries.  │
│                   │  def get_user(username):            │                          │
│                   │    query = f"SELECT * FROM users    │  HIGH: Hardcoded Secret  │
│                   │      WHERE username='{username}'"   │  Line 12 — API_KEY must  │
│                   │    cursor.execute(query)             │  be in an env variable.  │
│                   │                                     │                          │
│                   │                                     │  ⏱ 4.3s  │ Copilot CLI  │
├───────────────────┴─────────────────────────────────────┴──────────────────────────┤
│  D Devil  L Learn  R Review  G Git  C Conflicts  B Blueprint  Esc  ?  Q            │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Features

### 6 AI-Powered Modes

| Key | Mode | What It Does |
|-----|------|-------------|
| `D` | **Devil Mode** | Penetration-tester persona — finds SQL injection, hardcoded secrets, command injection, path traversal, weak cryptography, and logic flaws |
| `L` | **Learn Mode** | Patient-teacher persona — explains what the file does, key concepts, best practices, and learning opportunities |
| `R` | **Review Mode** | Senior-developer persona — full code quality review with a 0–10 score and verdict: Production Ready / Needs Work / Major Issues |
| `G` | **Git Review** | Pre-commit diff review scoped to the **selected file only** — catches bugs before they reach the repo |
| `C` | **Conflicts** | Merge conflict resolver — explains both sides of every conflict block and recommends the correct resolution |
| `B` | **Blueprint** | Instant full-project structure map — classes, functions, CSS selectors, JSON keys, CSV columns, HTML structure, all grouped by folder |

### Platform Features

- ✅ **Non-blocking UI** — all AI calls run in background threads via Textual workers; the interface never freezes mid-analysis
- ✅ **Selectable results** — click-drag to select, Ctrl+A, Ctrl+C to copy any part of the output
- ✅ **Instant Blueprint** — zero AI wait time; pure local parsing renders immediately for any project size
- ✅ **Universal file parsing** — 40+ programming languages (Python, JS/TS, Java, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, C/C++) plus CSS selectors, HTML structure, JSON keys, CSV columns, YAML keys
- ✅ **Smart truncation** — strips comment-only lines before hard-cutting at 800 lines; maximises signal sent to the AI
- ✅ **Startup preflight** — validates `gh`, Copilot extension, and auth on every launch with clear actionable fix messages
- ✅ **Binary-safe** — never crashes on `.png`, `.exe`, `.db`, or any non-text file
- ✅ **Works everywhere** — VS Code integrated terminal, Vim/Neovim split, SSH sessions, cloud dev boxes, Windows Terminal, iTerm2, Alacritty

---

## Tech Stack

| Technology | Role |
|------------|------|
| **Python 3.10+** | Core language |
| **[Textual](https://textual.textualize.io/)** | Terminal UI framework — 3-panel layout, key bindings, CSS theming, background workers |
| **[GitHub Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli)** (`gh copilot -p`) | AI engine powering all 6 analysis modes |
| **`ast`** | Python standard library — zero-dependency structural parsing for Blueprint Mode |
| **`re`** | Regex-based universal parser for JS, CSS, HTML, JSON, CSV, and 30+ other file types |
| **`subprocess`** | Runs Copilot CLI and git commands; `CREATE_NO_WINDOW` flag for Windows compatibility |
| **`pathlib`** | Cross-platform file handling and extension detection |
| **`tempfile`** | Secure temp files for Copilot to analyse; always cleaned up in `finally` blocks |
| **Git** | `git diff --staged -- <file>` scoped to the selected file for Git Review Mode |

---

## Project Structure

```
codesensei/
├── app.py                   # Entry point — path resolution, --help, --version, preflight checks
├── requirements.txt         # Single dependency: textual>=0.47.0
└── codesensei/
    ├── __init__.py          # Package marker — version 1.0
    ├── ui.py                # Textual TUI — 3-panel layout, 6 mode bindings, dark theme
    ├── copilot.py           # GitHub Copilot CLI integration — prompts, sanitization, parsing
    ├── scanner.py           # File metadata, git utilities, multi-language AST + regex parser
    └── preflight.py         # Startup dependency validator
```

---

## How It Works

```
┌──────────────────┐   key press    ┌─────────────────────┐   gh copilot -p   ┌──────────────────────┐
│   File Tree      │ ─────────────► │  Background Worker  │ ────────────────► │  GitHub Copilot CLI  │
│  (select a file) │                │  (@work thread=True) │                   │  (AI engine)         │
│                  │ ◄───────────── │                     │ ◄──────────────── │                      │
└──────────────────┘  results panel └─────────────────────┘  parsed response  └──────────────────────┘
                         updates
```

Every AI mode follows the same four-step pattern:

1. Code or diff is written to a **secure temporary file**
2. A **specialist persona prompt** is sent to `gh copilot -p` (penetration tester, teacher, senior dev, etc.)
3. The response is **parsed and sanitised** — internal tool-use lines stripped, markup removed
4. Output is loaded into the **selectable results panel** and the temp file is deleted in a `finally` block

Blueprint Mode skips the AI entirely — the class diagram is built locally from `ast.parse()` and regex, rendering instantly regardless of project size.

---

## Prerequisites

Before installing CodeSensei, ensure the following are in place:

| Requirement | Minimum Version | Check Command | Notes |
|-------------|----------------|---------------|-------|
| Python | 3.10+ | `python --version` | 3.12 recommended |
| GitHub CLI (`gh`) | 2.0+ | `gh --version` | Required for all AI modes |
| Copilot CLI extension | Latest | `gh extension list` | Install via `gh extension install github/gh-copilot` |
| GitHub authentication | — | `gh auth status` | Must be logged in |
| GitHub Copilot subscription | — | — | Free for students via [GitHub Student Pack](https://education.github.com/pack) |

> **No Copilot subscription yet?**
> - Students: Apply at [education.github.com/pack](https://education.github.com/pack) — includes free Copilot access
> - Everyone else: [github.com/features/copilot](https://github.com/features/copilot) — free trial available
> - Blueprint Mode works without any subscription — it's 100% local parsing

---

## Installation

### Step 1 — Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/codesensei.git
cd codesensei
```

> **No git?** Download the ZIP from the GitHub repo page → Code → Download ZIP, then extract it.

---

### Step 2 — Set Up a Python Virtual Environment (Recommended)

Using a virtual environment keeps CodeSensei's dependencies isolated from your system Python.

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> **How to tell it's active:** Your terminal prompt will show `(venv)` at the start.
>
> **To deactivate when done:** just run `deactivate`
>
> **Skipping venv?** You can install globally with `pip install -r requirements.txt` but this may conflict with other projects.

---

### Step 3 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs one package: `textual>=0.47.0` — the terminal UI framework.

> **Slow install?** Use a mirror: `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
>
> **Behind a corporate proxy?** `pip install -r requirements.txt --proxy http://proxy.company.com:8080`

---

### Step 4 — Install GitHub CLI

GitHub CLI (`gh`) is the engine that runs all AI analysis. Install it for your platform:

**Windows:**
```bash
winget install --id GitHub.cli
```
Or download the installer from [cli.github.com](https://cli.github.com).

**macOS:**
```bash
brew install gh
```

**Linux (Ubuntu / Debian):**
```bash
(type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
&& sudo mkdir -p -m 755 /etc/apt/keyrings \
&& wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
&& sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
&& sudo apt update \
&& sudo apt install gh -y
```

**Linux (Fedora / RHEL):**
```bash
sudo dnf install gh
```

Verify the install:
```bash
gh --version
# Expected: gh version 2.x.x (...)
```

---

### Step 5 — Install the Copilot CLI Extension

```bash
gh extension install github/gh-copilot
```

Verify:
```bash
gh extension list
# Should show: github/gh-copilot
```

> **Extension already installed?** Update it:
> ```bash
> gh extension upgrade gh-copilot
> ```

---

### Step 6 — Authenticate with GitHub

```bash
gh auth login
```

You will be prompted with a series of choices. Select:

```
? What account do you want to log into?  → GitHub.com
? What is your preferred protocol?        → HTTPS
? How would you like to authenticate?     → Login with a web browser
```

A one-time code like `ABCD-1234` will appear. Your browser opens automatically — paste the code and authorise.

Verify authentication:
```bash
gh auth status
# Expected: ✓ Logged in to github.com as YOUR-USERNAME
```

---

### SSH / Headless Server Authentication (No Browser Available)

When running CodeSensei on a remote server, cloud VM, Docker container, or any environment without a browser, the standard `gh auth login` flow won't work. Use one of these methods instead:

#### Method 1 — Device Flow (Recommended for SSH sessions)

```bash
gh auth login
```

Select:
```
? What account do you want to log into?  → GitHub.com
? What is your preferred protocol?        → HTTPS
? How would you like to authenticate?     → Login with a web browser
```

You'll see output like:
```
! First copy your one-time code: ABCD-1234
- Press Enter to open github.com in your browser...
```

**Do NOT press Enter on the server.** Instead:

1. Open [github.com/login/device](https://github.com/login/device) on your **local machine**
2. Enter the code `ABCD-1234`
3. Click Authorise
4. Back on the server — press Enter

The server will detect the completed auth and log in.

#### Method 2 — Personal Access Token (Best for automation / CI)

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens) → Generate new token (classic)
2. Select scopes: `repo`, `read:org`, `gist`
3. Copy the token

```bash
echo "YOUR_TOKEN_HERE" | gh auth login --with-token
```

Verify:
```bash
gh auth status
```

#### Method 3 — Environment Variable (Docker / CI pipelines)

```bash
export GH_TOKEN=your_personal_access_token
```

Or add it to your `.bashrc` / `.zshrc` for persistence:
```bash
echo 'export GH_TOKEN=your_token_here' >> ~/.bashrc
source ~/.bashrc
```

> **Important:** Never hardcode tokens in files. Use environment variables or a secrets manager.

#### Troubleshooting SSH Auth

| Issue | Fix |
|-------|-----|
| `gh auth login` hangs after showing the code | The device flow is waiting — complete it on your local browser, then press Enter on the server |
| `Error: authentication required` after auth | Run `gh auth refresh` to renew the token |
| `ERRO[0000] no terminal` | Use `--with-token` method instead of the interactive flow |
| Auth works but Copilot returns 401 | Your account may not have Copilot enabled — check at [github.com/settings/copilot](https://github.com/settings/copilot) |
| Token expired | Re-run `gh auth login` or generate a new token |

---

## Running CodeSensei

### Basic Launch

```bash
# Point at any project folder
python app.py /path/to/your/project

# Point at a relative path
python app.py ../my-other-project

# Launch on the current directory
python app.py

# Windows example
python app.py "C:\Users\YourName\Desktop\my-project"
```

> **Path has spaces?** Always wrap it in quotes:
> ```bash
> python app.py "C:\Users\John Smith\Projects\my app"
> ```

### Check Version / Help

```bash
python app.py --version    # prints: CodeSensei v1.0
python app.py --help       # full usage guide
```

### Using a Virtual Environment

If you set up a venv in Step 2, always activate it before running:

```bash
# Windows
venv\Scripts\activate
python app.py /path/to/project

# macOS / Linux
source venv/bin/activate
python app.py /path/to/project
```

### Running on an SSH Server

```bash
ssh user@your-server
cd /path/to/codesensei
source venv/bin/activate
python app.py /path/to/your/project
```

> **Terminal requirement:** Your SSH client must support UTF-8 and ANSI colours.
> - **PuTTY:** Settings → Window → Translation → UTF-8; Colours → Allow terminal to use xterm 256-colour mode
> - **Windows Terminal / iTerm2 / Alacritty:** Works out of the box
> - **VS Code Remote SSH:** Works out of the box in the integrated terminal

---

## Usage

### Keyboard Shortcuts

| Key | Mode | Works On |
|-----|------|---------|
| `D` | Devil Mode — security vulnerability scan | Selected file |
| `L` | Learn Mode — educational explanation | Selected file |
| `R` | Review Mode — code quality score (0–10) | Selected file |
| `G` | Git Review — staged diff review | Selected file (must be staged) |
| `C` | Conflicts — merge conflict resolution | Selected file (must have conflict markers) |
| `B` | Blueprint — full project structure map | Entire project (no file selection needed) |
| `Esc` | Cancel current analysis, restore file view | — |
| `?` | Help screen | — |
| `Q` | Quit | — |

### Navigation

- **Arrow keys** — move through the file tree
- **Enter** — select a file and load it into the code viewer
- **Click** — click any file in the tree to select it
- **Click + drag** in results panel — select text to copy
- **Ctrl+A** — select all results text
- **Ctrl+C** — copy selected results text

### Recommended Workflow

```
1. Open your project in your editor (VS Code, Vim, etc.)
2. Open a second terminal window in the same folder
3. Run: python app.py /path/to/your-project
4. Select any file in the CodeSensei file tree

   For security review:
   → Press D  (Devil Mode — finds vulnerabilities)
   → Press R  (Review Mode — quality score)

   Before committing:
   → git add yourfile.py  (stage the file in your other terminal)
   → Press G  (Git Review — AI reviews only your staged changes)

   For merge conflicts:
   → Press C  (Conflicts — AI explains both sides and recommends a resolution)

   For project overview:
   → Press B  (Blueprint — instant full project map, no file selection needed)
   → Press L on any file  (Learn Mode — understand unfamiliar code)

5. Use Esc at any time to cancel and return to the file view
6. Press Q to quit
```

### Git Review Mode — Step by Step

Git Review (`G`) reviews only the staged diff of the currently selected file. This is intentional — it gives you a focused, file-scoped review before you commit.

```bash
# 1. Make your changes in your editor
# 2. Stage the specific file
git add path/to/yourfile.py

# 3. In CodeSensei, select that same file in the tree
# 4. Press G
# → CodeSensei reviews only the changes you staged for that file
```

> **File not staged?** CodeSensei will show:
> `yourfile.py is not staged — run: git add yourfile.py`
> No confusion, no silent failures.

---

## Blueprint Mode — What It Shows

Blueprint (`B`) requires no file selection. It scans your entire project instantly and shows:

| File Type | What's Extracted |
|-----------|-----------------|
| `.py` | Classes, inheritance, methods with signatures and line numbers, module-level functions |
| `.js` / `.ts` | Classes (with extends/implements), async methods, arrow functions, named functions |
| `.java` / `.cs` / `.go` / `.rs` / `.rb` and 30+ more | Classes, structs, interfaces, functions/methods with signatures |
| `.html` | Page title, linked scripts, linked stylesheets, element IDs |
| `.css` / `.scss` | Class selectors, ID selectors, element selectors, media query count |
| `.json` | Package name/version, scripts, dependencies (for `package.json`); array length and field names for data files |
| `.csv` | Column headers and row count |
| `.yaml` / `.yml` | Top-level keys |
| `.md` | Section headings |

Files are grouped by folder. Binary files (images, executables, archives) are automatically skipped.

---

## Error Reference

CodeSensei never shows a raw stack trace. Every failure has a specific, actionable message:

| Scenario | What You See | Fix |
|----------|-------------|-----|
| No file selected | `Select a file first using the file tree` | Click a file in the left panel |
| File is empty | `File is empty — nothing to analyze` | Select a non-empty file |
| Binary file | `Binary file — cannot analyze` | Select a text/code file |
| File > 800 lines | `Large file — applying smart truncation...` | Analysis continues; bottom of file may not be included |
| Copilot quota exceeded (402) | Full instructions + settings link | Upgrade plan or wait for quota reset |
| Not authenticated (401) | `Run: gh auth login` | Re-authenticate with GitHub |
| Copilot not installed | `Run: gh extension install github/gh-copilot` | Install the extension |
| Analysis timed out | `Timed out — try a smaller file` | Select a smaller file or run again |
| File not staged (Git Review) | `yourfile.py is not staged — run: git add yourfile.py` | Stage the file first |
| No conflict markers (Conflicts) | `No merge conflicts found in this file` | Select a file with `<<<<<<<` markers |
| Not a git repo (Git Review) | `Not a git repository — run: git init` | Initialise a git repo in the project |

---

## Troubleshooting

### CodeSensei launches but AI modes return nothing

```bash
# Check Copilot CLI is working independently
gh copilot --version
gh auth status
```

If auth is fine but AI still fails, your Copilot subscription may be inactive:
→ [github.com/settings/copilot](https://github.com/settings/copilot)

### The terminal UI looks broken / garbled characters

CodeSensei requires UTF-8 and ANSI colour support.

```bash
# Force UTF-8 on Windows
set PYTHONIOENCODING=utf-8
python app.py /path/to/project

# Check your terminal supports colour
echo $TERM   # should be xterm-256color or similar
```

If using PuTTY: Settings → Window → Translation → Remote character set → UTF-8

### `python` command not found (Windows)

```bash
# Try python3 instead
python3 app.py /path/to/project

# Or use the full path
C:\Users\YourName\AppData\Local\Programs\Python\Python312\python.exe app.py .
```

### `gh: command not found` after installing GitHub CLI

The GitHub CLI binary is not on your PATH. Fix:

**Windows:** Restart your terminal after installing via `winget`.

**macOS/Linux:**
```bash
export PATH="$PATH:/usr/local/bin"
# Add to ~/.bashrc or ~/.zshrc to make permanent
```

### Copilot quota runs out (402 error)

Each Copilot CLI call counts against your monthly quota. If you hit the limit:
- **Students:** Quota resets monthly — check [github.com/settings/copilot](https://github.com/settings/copilot)
- **Paid plans:** Upgrade at [github.com/features/copilot](https://github.com/features/copilot)
- **While waiting:** Blueprint Mode works with zero quota — it's 100% local

### File tree is empty or missing files

Hidden directories (`.git`, `node_modules`, `__pycache__`, `.venv`, `dist`, `build`) are filtered out intentionally — this is expected behaviour.

---

## Compatibility

| Environment | Status | Notes |
|-------------|--------|-------|
| Windows 10/11 — Windows Terminal | ✅ Full support | Recommended terminal on Windows |
| Windows — Command Prompt | ⚠️ Limited | Colour support varies; use Windows Terminal instead |
| Windows — PowerShell | ✅ Full support | Works well |
| macOS — Terminal.app | ✅ Full support | |
| macOS — iTerm2 | ✅ Full support | |
| Linux — any modern terminal | ✅ Full support | |
| SSH sessions | ✅ Full support | Requires UTF-8 terminal on the client side |
| VS Code integrated terminal | ✅ Full support | |
| GitHub Codespaces | ✅ Full support | |
| Docker containers | ⚠️ Auth required | Run `gh auth login --with-token` inside the container |
| Jupyter terminals | ⚠️ Limited | Textual TUI may not render correctly in notebook terminals |

---

## License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
  Built with Python · Textual · GitHub Copilot CLI
</div>
