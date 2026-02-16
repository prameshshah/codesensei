import subprocess
import time
import tempfile
import os
import pathlib


def _file_suffix(filename: str) -> str:
    """Return the file extension to use for the temp file, defaulting to .txt."""
    suffix = pathlib.Path(filename).suffix
    return suffix if suffix else '.txt'


def check_copilot_installed():
    """Check if GitHub Copilot CLI is available"""
    try:
        result = subprocess.run(
            ["gh", "copilot", "--version"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def sanitize_code(content, max_lines=800):
    """Clean up code before sending to AI to avoid token limits.

    Returns (code_str, meta) where meta = {was_truncated, original_lines, comments_removed}.
    Strategy:
      1. Collapse consecutive blank lines.
      2. If still over limit, strip standalone comment-only lines (keeps more real code).
      3. Hard-truncate at max_lines if still needed.
    """
    if not content:
        return "", {'was_truncated': False, 'original_lines': 0, 'comments_removed': 0}

    lines = content.split('\n')
    original_line_count = len(lines)

    # Step 1: collapse consecutive blank lines
    cleaned = []
    prev_blank = False
    for line in lines:
        is_blank = line.strip() == ''
        if is_blank and prev_blank:
            continue
        cleaned.append(line)
        prev_blank = is_blank

    # Step 2: smart truncation — remove standalone comment lines to free space
    comments_removed = 0
    if len(cleaned) > max_lines:
        smart = []
        for line in cleaned:
            stripped = line.strip()
            # Remove pure comment lines; keep shebangs (#!) and keep inline comments
            if stripped.startswith('#') and not stripped.startswith('#!'):
                comments_removed += 1
                continue
            smart.append(line)
        cleaned = smart

    # Step 3: hard truncate if still over limit
    was_truncated = False
    if len(cleaned) > max_lines:
        cleaned = cleaned[:max_lines]
        cleaned.append(
            f"\n# ... (truncated at {max_lines} lines — original file: {original_line_count} lines)"
        )
        was_truncated = True

    meta = {
        'was_truncated': was_truncated,
        'original_lines': original_line_count,
        'comments_removed': comments_removed,
    }
    return '\n'.join(cleaned), meta


def _strip_tooluse(text: str) -> str:
    """Remove Copilot's internal tool-use step lines from a response.

    Handles all variants of Copilot's agentic tool output:
      ● Read app.py          — success tool call
      ✗ Edit auth.py         — failed tool call
      ✓ Created file.py      — completed tool call
        └ 17 lines read      — tool result
        $ pwsh command       — shell command run by Copilot
        Permission denied    — error output inside a tool block
        <exited with error>  — exit status inside a tool block
    """
    import re
    # Lines that open a tool block (●, •, ✗, ✓)
    _TOOL_START = re.compile(r'^\s*[●•✗✓]\s+\S')
    # Lines that are part of a tool block output (indented sub-lines)
    _TOOL_CONTENT = re.compile(
        r'^\s+('
        r'└'                   # result summary (└ N lines read)
        r'|\$\s'               # shell command ($ pwsh ...)
        r'|Permission'         # permission errors
        r'|<exited'            # exit status blocks
        r'|Error:'             # error messages
        r'|FullName'           # PowerShell output headers
        r'|IsReadOnly'
        r')'
    )

    lines = text.splitlines()
    filtered = []
    in_tool_block = False

    for line in lines:
        stripped = line.strip()

        if _TOOL_START.match(line):
            in_tool_block = True
            continue

        if in_tool_block:
            # Blank line ends the tool block
            if not stripped:
                in_tool_block = False
                continue
            # Indented tool output lines — skip
            if _TOOL_CONTENT.match(line):
                continue
            # Non-blank, non-tool-content line — end of tool block, keep this line
            in_tool_block = False

        filtered.append(line)

    # Collapse consecutive blank lines
    result = []
    prev_blank = False
    for line in filtered:
        is_blank = line.strip() == ''
        if is_blank and prev_blank:
            continue
        result.append(line)
        prev_blank = is_blank

    return '\n'.join(result).strip()


def call_copilot(prompt, timeout=60):
    """Call GitHub Copilot CLI. Returns structured dict with response, stats, timing."""
    cmd = ["gh", "copilot", "-p", prompt]
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    try:
        start = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=timeout,
            creationflags=flags
        )
        elapsed = time.time() - start

        if result.returncode == 0:
            return {
                'response': result.stdout.strip(),
                'stats': result.stderr.strip(),
                'command': ' '.join(cmd),
                'elapsed_ms': round(elapsed * 1000, 2),
                'success': True,
                'error': None
            }
        else:
            return {
                'response': '',
                'stats': result.stderr.strip(),
                'command': ' '.join(cmd),
                'elapsed_ms': round(elapsed * 1000, 2),
                'success': False,
                'error': result.stderr.strip()
            }

    except subprocess.TimeoutExpired:
        return {
            'response': '',
            'stats': '',
            'command': ' '.join(cmd),
            'elapsed_ms': timeout * 1000,
            'success': False,
            'error': f'timed out after {timeout}s'
        }
    except Exception as e:
        return {
            'response': '',
            'stats': '',
            'command': ' '.join(cmd),
            'elapsed_ms': 0,
            'success': False,
            'error': f'Error calling Copilot: {str(e)}'
        }


def summarize_file(file_content, filename):
    """Mode A: Generates a high-level overview."""
    clean_code, trunc_meta = sanitize_code(file_content)

    with tempfile.NamedTemporaryFile(mode='w', suffix=_file_suffix(filename), delete=False, encoding='utf-8') as f:
        f.write(clean_code)
        temp_path = f.name

    try:
        prompt = (
            f"Read the file at '{temp_path}'. Act as a patient teacher explaining to a junior developer.\n"
            "Cover:\n"
            "1. WHAT IT DOES — plain language summary\n"
            "2. KEY CONCEPTS — programming concepts used\n"
            "3. BEST PRACTICES — good things this code demonstrates\n"
            "4. LEARNING OPPORTUNITY — one thing to study further\n"
            "Keep it clear, friendly, and beginner-accessible."
        )
        result = call_copilot(prompt)
        result['truncation'] = trunc_meta
        return result
    finally:
        try:
            os.unlink(temp_path)  # Cleanup
        except:
            pass


def sanitize_diff(raw_diff: str) -> tuple:
    """Filter lockfiles/generated files and truncate to 400 code lines."""
    SKIP_PATTERNS = (
        'package-lock.json', 'yarn.lock', 'Pipfile.lock',
        'poetry.lock', 'Gemfile.lock', '.min.js', '.min.css',
        '.map', 'dist/', 'build/', 'coverage/',
    )
    MAX_CODE_LINES = 400

    sections = raw_diff.split('\ndiff --git ')
    kept_sections = []
    files_changed = 0
    lines_added = 0
    lines_removed = 0

    for i, section in enumerate(sections):
        header = ('diff --git ' + section) if i > 0 else section
        # Check if this section is a file we should skip
        first_line = section.split('\n')[0]
        if any(pat in first_line for pat in SKIP_PATTERNS):
            continue
        kept_sections.append(header)
        files_changed += 1

    clean_diff = '\n'.join(kept_sections)

    # Count and truncate actual code lines
    meta_prefixes = ('+++', '---', '@@', 'diff --git', 'index ', 'new file', 'deleted file')
    total_code = 0
    for line in clean_diff.splitlines():
        is_meta = any(line.startswith(p) for p in meta_prefixes)
        if not is_meta:
            total_code += 1
            if line.startswith('+') and not line.startswith('+++'):
                lines_added += 1
            elif line.startswith('-') and not line.startswith('---'):
                lines_removed += 1

    if total_code > MAX_CODE_LINES:
        truncated_lines = []
        code_count = 0
        for line in clean_diff.splitlines():
            is_meta = any(line.startswith(p) for p in meta_prefixes)
            if not is_meta:
                code_count += 1
                if code_count > MAX_CODE_LINES:
                    break
            truncated_lines.append(line)
        clean_diff = '\n'.join(truncated_lines)
        clean_diff += f'\n\n[Truncated: showing {MAX_CODE_LINES} of {total_code} code lines]'

    metadata = {
        'files_changed': files_changed,
        'lines_added': lines_added,
        'lines_removed': lines_removed,
        'truncated': total_code > MAX_CODE_LINES,
    }
    return clean_diff, metadata


def review_file(file_content: str, filename: str) -> dict:
    """Review mode: senior developer code review of a file."""
    clean_code, trunc_meta = sanitize_code(file_content)

    with tempfile.NamedTemporaryFile(mode='w', suffix=_file_suffix(filename), delete=False, encoding='utf-8') as f:
        f.write(clean_code)
        temp_path = f.name

    try:
        prompt = (
            f"Read the file at '{temp_path}'. You are a senior developer doing a thorough code review.\n"
            "Check for:\n"
            "1. BUGS — logic errors, edge cases, off-by-one, null/undefined handling\n"
            "2. QUALITY — naming, readability, dead code, overly complex logic\n"
            "3. SECURITY — injection, hardcoded secrets, missing input validation\n"
            "4. PERFORMANCE — unnecessary loops, repeated work, memory issues\n"
            "5. TESTS — which functions lack test coverage and why they need it\n"
            "End with a QUALITY SCORE (0-10) and a one-line verdict: "
            "Production Ready / Needs Work / Major Issues."
        )
        result = call_copilot(prompt)
        result['truncation'] = trunc_meta
        return result
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass


def review_diff(diff_content: str) -> dict:
    """Review mode: senior developer pre-commit review of git diff."""
    clean_diff, _ = sanitize_diff(diff_content)

    if not clean_diff.strip():
        return {
            'response': 'No reviewable changes found after filtering.',
            'stats': '', 'command': '', 'elapsed_ms': 0,
            'success': True, 'error': None,
        }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.diff', delete=False, encoding='utf-8') as f:
        f.write(clean_diff)
        temp_path = f.name

    try:
        prompt = (
            f"Read the git diff at '{temp_path}'. You are a senior developer doing a pre-commit review.\n"
            "Check for:\n"
            "1. SECURITY — injection, secrets, missing validation\n"
            "2. LOGIC — bugs, edge cases, division by zero\n"
            "3. QUALITY — naming, readability, dead code\n"
            "4. TESTS — missing test coverage for new functions\n"
            "5. BREAKING CHANGES — API changes, renamed functions\n"
            "Give a READINESS SCORE (0-10) and a one-line verdict: "
            "Ready to Commit / Needs Minor Work / Do Not Merge."
        )
        return call_copilot(prompt)
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass


def resolve_conflicts(file_content: str, filename: str) -> dict:
    """Conflict Resolution mode: explain and resolve git merge conflicts."""
    from codesensei.scanner import extract_conflicts
    conflicts = extract_conflicts(file_content)
    conflict_count = len(conflicts)

    with tempfile.NamedTemporaryFile(mode='w', suffix=_file_suffix(filename), delete=False, encoding='utf-8') as f:
        f.write(file_content)
        temp_path = f.name

    try:
        prompt = (
            f"Read the file at '{temp_path}'. It contains {conflict_count} git merge conflict(s). "
            "Do NOT ask any follow-up questions. Do NOT ask if I want you to solve them. "
            "Just immediately provide the full analysis and resolution now.\n\n"
            "For EACH conflict block (<<<<<<< HEAD ... >>>>>>> branch), output:\n"
            "1. CURRENT BRANCH — one sentence: what this code does\n"
            "2. INCOMING BRANCH — one sentence: what this code does\n"
            "3. RECOMMENDATION — which side to keep and exactly why\n"
            "4. RESOLVED — the resolved code snippet with no conflict markers\n\n"
            "Be concise and decisive. If both sides are needed, show the merged result."
        )
        result = call_copilot(prompt)
        result['conflict_count'] = conflict_count
        return result
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass



def blueprint_file(file_content: str, filename: str, structure: dict) -> dict:
    """Blueprint Mode: architectural analysis of a single file."""
    from codesensei.scanner import format_blueprint
    skeleton_lines = format_blueprint(structure, filename)

    lang = structure.get('language', 'code')

    if structure.get('supported') and not structure.get('error'):
        # Parsed file (Python AST or JS/TS regex) — send compact skeleton inline
        skeleton_text = '\n'.join(skeleton_lines)
        prompt = (
            f"You are a senior software architect reviewing a {lang} file named '{filename}'.\n"
            f"Here is the structure skeleton extracted from the file:\n\n"
            f"{skeleton_text}\n\n"
            "Do NOT repeat the skeleton back. Immediately provide:\n"
            "1. RESPONSIBILITIES — what each class/function is responsible for (one line each)\n"
            "2. DESIGN CONCERNS — SRP violations, god objects, missing abstractions, "
            "problematic inheritance, or suspicious dependency chains\n"
            "3. COUPLING — which classes/functions are tightly coupled and why that matters\n"
            "4. RECOMMENDATIONS — concrete refactoring suggestions (max 3, most impactful first)\n"
            "Be concise and decisive. No bullet padding."
        )
        result = call_copilot(prompt)
        result['skeleton'] = skeleton_lines
        return result
    else:
        # Unsupported language — embed raw source inline (avoids agentic read-then-ask loop)
        clean_code, _ = sanitize_code(file_content)
        ext = _file_suffix(filename).lstrip('.') or 'text'
        prompt = (
            f"You are a senior software architect reviewing a {ext} file named '{filename}'.\n"
            f"Here is the complete source:\n\n{clean_code}\n\n"
            "Immediately provide:\n"
            "1. STRUCTURE — list every class, its methods, and every top-level function with signatures\n"
            "2. RESPONSIBILITIES — one line per class/module on what it owns\n"
            "3. DESIGN CONCERNS — SRP violations, god objects, bad coupling, missing abstractions\n"
            "4. RECOMMENDATIONS — top 3 most impactful refactoring suggestions\n"
            "Be concise and decisive. No padding."
        )
        result = call_copilot(prompt)
        if result.get('success') and result.get('response'):
            result['response'] = _strip_tooluse(result['response'])
        result['skeleton'] = skeleton_lines
        return result


def blueprint_project(project: dict, project_name: str) -> dict:
    """Blueprint Mode: architectural analysis of an entire project's class structure."""
    from codesensei.scanner import format_project_blueprint

    skeleton_lines = format_project_blueprint(project, project_name)
    skeleton_text = '\n'.join(skeleton_lines)

    # Build a compact summary for the Copilot prompt (names + bases + method counts only)
    compact_parts = []
    for cls in project['all_classes']:
        bases_str = f"({', '.join(cls['bases'])})" if cls['bases'] else ""
        method_names = [m['name'] for m in cls['methods']]
        compact_parts.append(
            f"  [{cls['file']}] class {cls['name']}{bases_str}: "
            f"{', '.join(method_names) if method_names else 'no methods'}"
        )

    compact_skeleton = '\n'.join(compact_parts) if compact_parts else "(no classes found — procedural codebase)"

    prompt = (
        f"You are a senior software architect reviewing the class structure of a project called '{project_name}'.\n"
        f"Here is the complete class inventory extracted from the source:\n\n"
        f"{compact_skeleton}\n\n"
        "Do NOT list the classes back. Immediately provide:\n"
        "1. ARCHITECTURE SUMMARY — one paragraph: what kind of system this is and how it is structured\n"
        "2. DESIGN CONCERNS — SRP violations, god classes, missing abstractions, suspicious inheritance, "
        "classes that should be split or merged\n"
        "3. COUPLING — which classes are too tightly coupled and why it matters\n"
        "4. RECOMMENDATIONS — top 3 most impactful architectural improvements, most critical first\n"
        "Be concise and decisive. No padding."
    )

    result = call_copilot(prompt)
    if result.get('success') and result.get('response'):
        result['response'] = _strip_tooluse(result['response'])
    result['skeleton'] = skeleton_lines
    return result


def devil_analyze(file_content, filename):
    """Mode B (Devil's Advocate): Aggressive security analysis."""
    clean_code, trunc_meta = sanitize_code(file_content)

    with tempfile.NamedTemporaryFile(mode='w', suffix=_file_suffix(filename), delete=False, encoding='utf-8') as f:
        f.write(clean_code)
        temp_path = f.name

    try:
        prompt = (
            f"Read the file at '{temp_path}'. You are a penetration tester doing a hostile security review.\n"
            "Find: SQL injection, hardcoded secrets, missing input validation, "
            "logic bugs, race conditions, weak crypto, insecure defaults.\n"
            "For each issue: rate severity (HIGH/MEDIUM/LOW), give the line number, "
            "show an exploit example, and suggest a specific fix.\n"
            "If no issues found, say: NO ISSUES FOUND."
        )
        result = call_copilot(prompt)
        result['truncation'] = trunc_meta
        return result
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass
