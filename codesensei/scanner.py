import ast
import pathlib
import subprocess
import os


def get_staged_diff(repo_path: str) -> dict:
    """Run git diff --staged and return structured result."""
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    # Check if it's a git repo
    try:
        check = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, encoding='utf-8',
            timeout=5, creationflags=flags, cwd=repo_path
        )
        if check.returncode != 0:
            return {'diff': '', 'has_changes': False, 'is_git_repo': False, 'error': None}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {'diff': '', 'has_changes': False, 'is_git_repo': False, 'error': 'git not found'}

    # Get staged diff
    try:
        result = subprocess.run(
            ["git", "diff", "--staged"],
            capture_output=True, text=True, encoding='utf-8',
            timeout=10, creationflags=flags, cwd=repo_path
        )
        diff = result.stdout.strip()
        return {
            'diff': diff,
            'has_changes': bool(diff),
            'is_git_repo': True,
            'error': None,
        }
    except Exception as e:
        return {'diff': '', 'has_changes': False, 'is_git_repo': True, 'error': str(e)}


def format_size(size_bytes):
    """Helper to make file sizes human-readable"""
    if size_bytes > 1024 * 1024:
        return f"{size_bytes / 1024 / 1024:.2f} MB"
    elif size_bytes > 1024:
        return f"{size_bytes / 1024:.2f} KB"
    return f"{size_bytes} bytes"


def get_staged_files(repo_path: str) -> list:
    """Return list of relative paths that are currently staged."""
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        result = subprocess.run(
            ["git", "diff", "--staged", "--name-only"],
            capture_output=True, text=True, encoding='utf-8',
            timeout=5, creationflags=flags, cwd=repo_path
        )
        if result.returncode == 0:
            return [f for f in result.stdout.strip().splitlines() if f]
    except Exception:
        pass
    return []


def get_staged_diff_for_file(repo_path: str, file_path: str) -> dict:
    """Get staged diff for a specific file only."""
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    # Get relative path of the file from repo root
    try:
        rel = pathlib.Path(file_path).resolve().relative_to(
            pathlib.Path(repo_path).resolve()
        )
        rel_str = rel.as_posix()
    except ValueError:
        return {'diff': '', 'has_changes': False, 'is_git_repo': True, 'error': 'File is outside repo'}

    try:
        check = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, encoding='utf-8',
            timeout=5, creationflags=flags, cwd=repo_path
        )
        if check.returncode != 0:
            return {'diff': '', 'has_changes': False, 'is_git_repo': False, 'error': None}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {'diff': '', 'has_changes': False, 'is_git_repo': False, 'error': 'git not found'}

    try:
        result = subprocess.run(
            ["git", "diff", "--staged", "--", rel_str],
            capture_output=True, text=True, encoding='utf-8',
            timeout=10, creationflags=flags, cwd=repo_path
        )
        diff = result.stdout.strip()
        return {
            'diff': diff,
            'has_changes': bool(diff),
            'is_git_repo': True,
            'error': None,
            'filename': rel_str,
        }
    except Exception as e:
        return {'diff': '', 'has_changes': False, 'is_git_repo': True, 'error': str(e)}


def has_merge_conflicts(file_content: str) -> bool:
    """Return True if the file content contains git merge conflict markers."""
    return '<<<<<<<' in file_content


def extract_conflicts(file_content: str) -> list:
    """Parse conflict markers and return a list of conflict dicts.

    Each dict has keys: 'current' (HEAD side), 'incoming' (branch side), 'branch' (branch name).
    """
    conflicts = []
    lines = file_content.split('\n')
    state = None  # 'current' or 'incoming'
    current_lines = []
    incoming_lines = []
    branch_name = ''

    for line in lines:
        if line.startswith('<<<<<<<'):
            state = 'current'
            current_lines = []
            incoming_lines = []
            branch_name = line[7:].strip()
        elif line.startswith('=======') and state == 'current':
            state = 'incoming'
        elif line.startswith('>>>>>>>') and state == 'incoming':
            conflicts.append({
                'current': '\n'.join(current_lines),
                'incoming': '\n'.join(incoming_lines),
                'branch': branch_name,
            })
            state = None
            current_lines = []
            incoming_lines = []
            branch_name = ''
        elif state == 'current':
            current_lines.append(line)
        elif state == 'incoming':
            incoming_lines.append(line)

    return conflicts


def _parse_js_ts(content: str, filename: str) -> dict:
    """Regex-based structural parser for JavaScript and TypeScript files.

    Returns the same dict shape as the Python AST parser so format_blueprint()
    and blueprint_file() work identically for all languages.
    """
    import re

    lines = content.splitlines()
    imports = []
    classes = []
    functions = []

    # Imports: ES6 import or CommonJS require
    IMPORT_RE = re.compile(r'^\s*import\s+')
    REQUIRE_RE = re.compile(r'^\s*(?:const|let|var)\s+\S.*?=\s*require\s*\(')
    for line in lines:
        if IMPORT_RE.match(line) or REQUIRE_RE.match(line):
            imports.append(line.strip())

    # Class: [export] [abstract] class Name [extends Base] [implements ...]
    CLASS_RE = re.compile(
        r'^(?:export\s+(?:default\s+)?)?(?:abstract\s+)?class\s+(\w+)'
        r'(?:\s+extends\s+([\w$.]+))?'
        r'(?:\s+implements\s+[\w,\s<>]+)?'
        r'\s*\{'
    )

    # Method inside a class: must be indented, optional modifiers
    METHOD_RE = re.compile(
        r'^( {2,}|\t+)'
        r'(?:(?:public|private|protected|override|readonly|static|abstract|declare)\s+)*'
        r'(?:async\s+)?(?:get\s+|set\s+)?'
        r'(\w+)\s*[<(]'   # name followed by < (generic) or ( (params)
    )

    SKIP_KEYWORDS = {
        'if', 'else', 'for', 'while', 'switch', 'catch', 'try', 'do',
        'return', 'case', 'default', 'new', 'typeof', 'instanceof',
        'throw', 'delete', 'void', 'yield', 'await',
    }

    # Top-level: function name(params) or async function name(params)
    FUNC_RE = re.compile(
        r'^(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)'
    )
    # Top-level: const/let/var name = (...) => or = async (...) =>
    ARROW_RE = re.compile(
        r'^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[\w]+)\s*=>'
    )
    # Top-level: const name = function(...)
    CONST_FUNC_RE = re.compile(
        r'^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function\s*\('
    )

    # Walk lines tracking brace depth to know class scope
    class_stack = []   # list of (class_dict, entry_depth)
    seen_funcs = set()
    depth = 0

    for lineno, raw_line in enumerate(lines, 1):
        stripped = raw_line.strip()
        open_b = raw_line.count('{') - raw_line.count('`')  # rough; good enough for most files
        open_b = raw_line.count('{')
        close_b = raw_line.count('}')

        # Class declaration
        class_m = CLASS_RE.match(stripped)
        if class_m:
            cls = {
                'name': class_m.group(1),
                'bases': [class_m.group(2)] if class_m.group(2) else [],
                'lineno': lineno,
                'methods': [],
            }
            classes.append(cls)
            class_stack.append((cls, depth))
            depth += open_b - close_b
            continue

        depth += open_b - close_b

        # Pop classes whose brace scope has closed
        while class_stack and depth <= class_stack[-1][1]:
            class_stack.pop()

        if class_stack:
            # Inside a class — look for methods
            method_m = METHOD_RE.match(raw_line)
            if method_m:
                name = method_m.group(2)
                if name not in SKIP_KEYWORDS and not name[0].isupper():
                    # Extract params from the line
                    paren = raw_line.find('(', raw_line.find(name))
                    args = ''
                    if paren != -1:
                        end = raw_line.find(')', paren)
                        if end != -1:
                            args = raw_line[paren + 1:end].strip()
                    is_async = bool(re.search(r'\basync\b', raw_line[:raw_line.find(name)]))
                    class_stack[-1][0]['methods'].append({
                        'name': name,
                        'args': args,
                        'returns': '',
                        'lineno': lineno,
                        'is_async': is_async,
                    })
        else:
            # Top-level scope — look for functions
            func_m = FUNC_RE.match(stripped)
            if func_m and func_m.group(1) not in seen_funcs:
                seen_funcs.add(func_m.group(1))
                is_async = 'async' in stripped[:stripped.index('function')]
                functions.append({
                    'name': func_m.group(1),
                    'args': func_m.group(2).strip(),
                    'returns': '',
                    'lineno': lineno,
                    'is_async': is_async,
                })
                continue

            arrow_m = ARROW_RE.match(stripped) or CONST_FUNC_RE.match(stripped)
            if arrow_m and arrow_m.group(1) not in seen_funcs:
                name = arrow_m.group(1)
                seen_funcs.add(name)
                args_m = re.search(r'\(([^)]*)\)\s*(?:=>|{)', stripped)
                args = args_m.group(1).strip() if args_m else ''
                functions.append({
                    'name': name,
                    'args': args,
                    'returns': '',
                    'lineno': lineno,
                    'is_async': 'async' in stripped,
                })

    suffix = pathlib.Path(filename).suffix.lower()
    lang = 'TypeScript' if suffix in ('.ts', '.tsx') else 'JavaScript'

    return {
        'supported': True,
        'language': lang,
        'error': None,
        'imports': imports[:8],
        'classes': classes,
        'functions': functions,
    }


_LANG_MAP = {
    '.java': 'Java',        '.cs': 'C#',          '.go': 'Go',
    '.rs': 'Rust',          '.rb': 'Ruby',         '.php': 'PHP',
    '.swift': 'Swift',      '.kt': 'Kotlin',       '.kts': 'Kotlin',
    '.scala': 'Scala',      '.c': 'C',             '.cpp': 'C++',
    '.cc': 'C++',           '.cxx': 'C++',         '.h': 'C/C++ Header',
    '.hpp': 'C++ Header',   '.dart': 'Dart',       '.lua': 'Lua',
    '.r': 'R',              '.m': 'Objective-C',   '.ex': 'Elixir',
    '.exs': 'Elixir',       '.hs': 'Haskell',      '.ml': 'OCaml',
    '.fs': 'F#',            '.fsx': 'F#',          '.sh': 'Shell',
    '.bash': 'Shell',       '.zsh': 'Shell',       '.sql': 'SQL',
    '.yaml': 'YAML',        '.yml': 'YAML',        '.json': 'JSON',
    '.toml': 'TOML',        '.xml': 'XML',         '.html': 'HTML',
    '.css': 'CSS',          '.scss': 'SCSS',       '.md': 'Markdown',
    '.tf': 'Terraform',     '.proto': 'Protobuf',  '.graphql': 'GraphQL',
    '.gql': 'GraphQL',      '.vue': 'Vue',         '.svelte': 'Svelte',
}


def _extract_args(raw_line: str, name: str) -> str:
    """Return the argument string from the first '(...)' after `name`."""
    import re
    name_pos = raw_line.find(name)
    if name_pos == -1:
        return ''
    paren = raw_line.find('(', name_pos)
    if paren == -1:
        return ''
    end = raw_line.find(')', paren)
    return raw_line[paren + 1:end].strip() if end != -1 else ''


def _parse_generic(content: str, filename: str) -> dict:
    """Universal regex-based structural parser covering Java, C#, Go, Rust,
    Ruby, PHP, Swift, Kotlin, C/C++, Scala, Dart, Lua, Shell, and more.

    Returns the same dict shape as the Python/JS parsers so format_blueprint()
    and blueprint_file() work identically for every language.
    """
    import re

    lines = content.splitlines()
    imports = []
    classes = []
    functions = []

    suffix = pathlib.Path(filename).suffix.lower()

    # ── Import / using / include detection ────────────────────────────────────
    IMPORT_RE = re.compile(
        r'^\s*(?:import|using|#include|require|use\s|from\s|package\s|'
        r'extern\s+crate|mod\s|include\s|load\s|source\s)\s*\S'
    )
    for line in lines:
        s = line.strip()
        if IMPORT_RE.match(line) and not s.startswith('//') and not s.startswith('#!'):
            imports.append(s)

    # ── Class patterns ────────────────────────────────────────────────────────
    # Main: class/struct/interface/trait/enum/... Name [any inheritance] [{|EOL]
    CLASS_RE = re.compile(
        r'^(?:(?:public|private|protected|internal|abstract|final|sealed|'
        r'open|data|inner|companion|value|inline|external|expect|actual|'
        r'static|async|partial|unsafe|new)\s+)*'
        r'(?:class|struct|interface|trait|enum|record|object|module|'
        r'namespace|protocol|extension|mixin|singleton)\s+(\w+)'
        r'[^{;\n]*'           # extends, implements, :, generics — anything before {
        r'\s*(?:\{|$)'        # opening brace or end of line (Ruby/Python-like)
    )
    # Go: type Name struct { or type Name interface {
    GO_TYPE_RE = re.compile(r'^type\s+(\w+)\s+(?:struct|interface)\s*\{')
    # Rust: impl [Trait for] TypeName [<generics>] {
    RUST_IMPL_RE = re.compile(r'^(?:pub(?:\([^)]*\))?\s+)?impl(?:\s+\S+\s+for)?\s+(\w+)')

    # ── Function / method patterns ─────────────────────────────────────────────
    # Keyword-style: func/fun/fn/def/function/sub/proc/method Name(
    FUNC_KW_RE = re.compile(
        r'^(?:(?:public|private|protected|internal|static|final|abstract|'
        r'async|override|virtual|unsafe|extern|native|inline|const|pure|'
        r'open|operator|infix|tailrec|suspend|companion|pub|priv)\s+)*'
        r'(?:func|fun|fn|def|function|sub|proc|method|operator)\s+(\w+)\s*[<(]'
    )
    # Java/C# indented method: [modifiers] ReturnType name(params) {
    JAVA_METH_RE = re.compile(
        r'^(?:\s{2,}|\t+)'
        r'(?:(?:public|private|protected|static|final|abstract|async|override|'
        r'virtual|new|sealed|readonly|synchronized|native|volatile)\s+)+'
        r'(?:[\w<>\[\]?*&]+\s+){1,4}'
        r'(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{'
    )
    # Go receiver method: func (recv Type) Name(
    GO_RECV_RE = re.compile(r'^func\s+\((\w+)\s+([\w*]+)\)\s+(\w+)\s*\(([^)]*)\)')
    # Go plain function: func Name(
    GO_FUNC_RE = re.compile(r'^func\s+(\w+)\s*\(([^)]*)\)')

    SKIP = {
        'if', 'else', 'for', 'while', 'switch', 'match', 'catch', 'try', 'do',
        'return', 'case', 'default', 'new', 'typeof', 'instanceof', 'throw',
        'delete', 'void', 'yield', 'await', 'where', 'select', 'from', 'when',
        'let', 'var', 'const', 'loop', 'unsafe', 'move', 'mut', 'ref', 'in',
        'with', 'as', 'of', 'by', 'on', 'is', 'not', 'and', 'or',
        'True', 'False', 'None', 'null', 'nil', 'true', 'false',
        'main', 'init', 'begin', 'end', 'do', 'puts', 'print', 'printf',
    }

    # class_stack entries: (class_dict, entry_brace_depth, class_line_indent, brace_mode)
    # brace_mode=True  → scope tracked by {} depth
    # brace_mode=False → scope tracked by `end` keyword at same indentation (Ruby etc.)
    class_stack = []
    seen_funcs = set()
    # Map type_name → class_dict for Rust impl merging
    class_by_name: dict = {}
    depth = 0

    is_ruby = suffix == '.rb'
    is_go = suffix == '.go'
    is_rust = suffix == '.rs'

    for lineno, raw_line in enumerate(lines, 1):
        stripped = raw_line.strip()
        line_indent = len(raw_line) - len(raw_line.lstrip())

        if not stripped:
            depth += raw_line.count('{') - raw_line.count('}')
            continue

        open_b = raw_line.count('{')
        close_b = raw_line.count('}')

        # ── Ruby `end` closes the current class scope ──────────────────────────
        if class_stack and not class_stack[-1][3]:  # non-brace mode
            if stripped == 'end' and line_indent <= class_stack[-1][2]:
                class_stack.pop()
                depth += open_b - close_b
                continue

        # ── Go: type Name struct / interface ──────────────────────────────────
        if is_go:
            go_type_m = GO_TYPE_RE.match(stripped)
            if go_type_m:
                name = go_type_m.group(1)
                cls = {'name': name, 'bases': [], 'lineno': lineno, 'methods': []}
                classes.append(cls)
                class_by_name[name] = cls
                class_stack.append((cls, depth, line_indent, True))
                depth += open_b - close_b
                continue

            # Go receiver method → attach to struct
            recv_m = GO_RECV_RE.match(stripped)
            if recv_m:
                type_name = recv_m.group(2).lstrip('*')
                name = recv_m.group(3)
                args = recv_m.group(4).strip()
                if name not in SKIP:
                    if type_name in class_by_name:
                        class_by_name[type_name]['methods'].append({
                            'name': name, 'args': args, 'returns': '',
                            'lineno': lineno, 'is_async': False,
                        })
                    else:
                        # struct not yet seen — create placeholder
                        cls = {'name': type_name, 'bases': [], 'lineno': lineno, 'methods': []}
                        classes.append(cls)
                        class_by_name[type_name] = cls
                        cls['methods'].append({
                            'name': name, 'args': args, 'returns': '',
                            'lineno': lineno, 'is_async': False,
                        })
                depth += open_b - close_b
                continue

            # Go plain function
            go_fn_m = GO_FUNC_RE.match(stripped)
            if go_fn_m:
                name = go_fn_m.group(1)
                if name not in SKIP and name not in seen_funcs:
                    seen_funcs.add(name)
                    functions.append({
                        'name': name, 'args': go_fn_m.group(2).strip(), 'returns': '',
                        'lineno': lineno, 'is_async': False,
                    })
                depth += open_b - close_b
                continue

        # ── Rust impl block → merge methods into existing struct ───────────────
        if is_rust and stripped.startswith('impl'):
            impl_m = RUST_IMPL_RE.match(stripped)
            if impl_m:
                type_name = impl_m.group(1)
                if type_name not in SKIP:
                    if type_name in class_by_name:
                        target = class_by_name[type_name]
                    else:
                        target = {'name': type_name, 'bases': [], 'lineno': lineno, 'methods': []}
                        classes.append(target)
                        class_by_name[type_name] = target
                    class_stack.append((target, depth, line_indent, True))
                    depth += open_b - close_b
                    continue

        # ── Class / struct / … declaration ────────────────────────────────────
        class_m = CLASS_RE.match(stripped)
        if class_m:
            name = class_m.group(1)
            if name not in SKIP:
                bases = []
                base_m = re.search(
                    r'(?:extends|implements|inherits|<|:(?!:))\s*([\w, .<>]+?)(?:\s*\{|$|\s+where)',
                    stripped
                )
                if base_m:
                    raw_bases = re.sub(r'<[^>]*>', '', base_m.group(1))
                    bases = [b.strip() for b in raw_bases.split(',') if b.strip() and b.strip() not in SKIP]
                uses_brace = open_b > 0
                cls = {'name': name, 'bases': bases, 'lineno': lineno, 'methods': []}
                classes.append(cls)
                class_by_name[name] = cls
                class_stack.append((cls, depth, line_indent, uses_brace))
                depth += open_b - close_b
                continue

        depth += open_b - close_b

        # ── Pop brace-tracked classes whose scope closed ───────────────────────
        while class_stack and class_stack[-1][3] and depth <= class_stack[-1][1]:
            class_stack.pop()

        # ── Method or top-level function ───────────────────────────────────────
        # Keyword-style (def, fn, func, fun, function, …)
        kw_m = FUNC_KW_RE.match(stripped)
        if kw_m:
            name = kw_m.group(1)
            if name not in SKIP:
                args = _extract_args(raw_line, name)
                is_async = bool(re.search(r'\basync\b', raw_line[:raw_line.find(name)]))
                entry = {'name': name, 'args': args, 'returns': '', 'lineno': lineno, 'is_async': is_async}
                if class_stack:
                    class_stack[-1][0]['methods'].append(entry)
                elif name not in seen_funcs:
                    seen_funcs.add(name)
                    functions.append(entry)
            continue

        # Java/C# indented method with return type
        if not is_ruby and not is_go and not is_rust:
            jm = JAVA_METH_RE.match(raw_line)
            if jm:
                name = jm.group(1)
                if name not in SKIP:
                    args = _extract_args(raw_line, name)
                    is_async = 'async' in raw_line[:raw_line.find(name)]
                    entry = {'name': name, 'args': args, 'returns': '', 'lineno': lineno, 'is_async': is_async}
                    if class_stack:
                        class_stack[-1][0]['methods'].append(entry)
                    elif name not in seen_funcs:
                        seen_funcs.add(name)
                        functions.append(entry)

    lang = _LANG_MAP.get(suffix, suffix.lstrip('.').upper() or 'Unknown')
    return {
        'supported': True,
        'language': lang,
        'error': None,
        'imports': imports[:8],
        'classes': classes,
        'functions': functions,
    }


def parse_structure(content: str, filename: str) -> dict:
    """Parse a file's structure and return a normalised dict.

    Dispatches to:
      .py               → Python AST (precise)
      .js .jsx .ts .tsx → dedicated JS/TS regex parser
      everything else   → universal _parse_generic() regex parser

    Returns:
      supported  – always True (every file gets best-effort parsing)
      language   – human-readable language name
      error      – str or None
      imports    – list[str]
      classes    – list[{name, bases, lineno, methods}]
      functions  – list[{name, args, returns, lineno, is_async}]
    """
    suffix = pathlib.Path(filename).suffix.lower()

    if suffix in ('.js', '.jsx', '.ts', '.tsx'):
        return _parse_js_ts(content, filename)

    if suffix != '.py':
        return _parse_generic(content, filename)

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return {
            'supported': True,
            'error': f"SyntaxError at line {e.lineno}: {e.msg}",
            'imports': [], 'classes': [], 'functions': [],
        }

    imports = []
    classes = []
    functions = []

    def _arg_str(arg: ast.arg) -> str:
        if arg.annotation:
            return f"{arg.arg}: {ast.unparse(arg.annotation)}"
        return arg.arg

    def _args_str(arguments: ast.arguments) -> str:
        parts = [_arg_str(a) for a in arguments.args]
        if arguments.vararg:
            parts.append(f"*{arguments.vararg.arg}")
        if arguments.kwarg:
            parts.append(f"**{arguments.kwarg.arg}")
        return ', '.join(parts)

    def _returns_str(node) -> str:
        if node.returns:
            return f" -> {ast.unparse(node.returns)}"
        return ''

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            else:
                mod = node.module or ''
                imports.append(mod)

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = [ast.unparse(b) for b in node.bases] if node.bases else []
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append({
                        'name': item.name,
                        'args': _args_str(item.args),
                        'returns': _returns_str(item),
                        'lineno': item.lineno,
                        'is_async': isinstance(item, ast.AsyncFunctionDef),
                    })
            classes.append({
                'name': node.name,
                'bases': bases,
                'lineno': node.lineno,
                'methods': methods,
            })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({
                'name': node.name,
                'args': _args_str(node.args),
                'returns': _returns_str(node),
                'lineno': node.lineno,
                'is_async': isinstance(node, ast.AsyncFunctionDef),
            })

    return {
        'supported': True,
        'language': 'Python',
        'error': None,
        'imports': list(dict.fromkeys(imports)),  # deduplicate, preserve order
        'classes': classes,
        'functions': functions,
    }


_PROJECT_IGNORE = {
    '.venv', 'venv', '__pycache__', '.git', 'node_modules',
    'env', '.env', 'dist', 'build', '.pytest_cache', 'coverage',
    'htmlcov', '.mypy_cache', '.tox', 'site-packages', '.idea', '.vscode',
}


_BINARY_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico',
    '.pdf', '.zip', '.tar', '.gz', '.rar', '.7z',
    '.exe', '.dll', '.so', '.dylib', '.bin',
    '.mp3', '.mp4', '.wav', '.avi', '.mov',
    '.pyc', '.pyd', '.whl', '.class', '.jar',
    '.ttf', '.otf', '.woff', '.woff2', '.eot',
    '.db', '.sqlite', '.sqlite3', '.lock',
}

_JS_TS_EXTS = {'.js', '.jsx', '.ts', '.tsx'}

# Extensions handled by _parse_file_summary (markup/data/config — no classes/functions)
_SUMMARY_EXTS = {
    '.html', '.htm', '.css', '.scss', '.sass',
    '.json', '.csv', '.yaml', '.yml', '.md', '.markdown',
    '.toml', '.xml', '.env', '.iml', '.graphql', '.gql', '.proto',
}

_CODE_EXTS = ({'.py'} | _JS_TS_EXTS | set(_LANG_MAP.keys())) - _SUMMARY_EXTS


def _parse_file_summary(content: str, filename: str) -> list:
    """Return a list of human-readable summary strings for non-code files."""
    import re, json as _json
    ext = pathlib.Path(filename).suffix.lower()
    items = []

    if ext in ('.json',):
        try:
            data = _json.loads(content[:200_000])  # cap at 200KB to avoid huge files
            if isinstance(data, dict):
                keys = list(data.keys())
                if 'name' in data and 'version' in data:
                    items.append(f"Package: {data.get('name')}  v{data.get('version')}")
                if 'scripts' in data and isinstance(data['scripts'], dict):
                    items.append(f"Scripts: {', '.join(data['scripts'].keys())}")
                if 'dependencies' in data and isinstance(data['dependencies'], dict):
                    deps = list(data['dependencies'].keys())
                    items.append(f"Dependencies ({len(deps)}): {', '.join(deps[:8])}" + (' ...' if len(deps) > 8 else ''))
                if 'devDependencies' in data and isinstance(data['devDependencies'], dict):
                    devdeps = list(data['devDependencies'].keys())
                    items.append(f"DevDependencies ({len(devdeps)}): {', '.join(devdeps[:6])}" + (' ...' if len(devdeps) > 6 else ''))
                if not items:
                    items.append(f"Keys: {', '.join(keys[:12])}" + (' ...' if len(keys) > 12 else ''))
            elif isinstance(data, list):
                items.append(f"Array: {len(data)} item(s)")
                if data and isinstance(data[0], dict):
                    fields = list(data[0].keys())
                    items.append(f"Fields: {', '.join(fields[:10])}" + (' ...' if len(fields) > 10 else ''))
        except Exception:
            pass  # skip unparseable JSON silently

    elif ext in ('.html', '.htm'):
        title = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if title:
            items.append(f"Title: {title.group(1).strip()}")
        scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE)
        if scripts:
            items.append(f"Scripts: {', '.join(scripts)}")
        links = re.findall(r'<link[^>]+href=["\']([^"\']+\.css)["\']', content, re.IGNORECASE)
        if links:
            items.append(f"Styles: {', '.join(links)}")
        ids = re.findall(r'\bid=["\']([^"\']+)["\']', content)
        if ids:
            items.append(f"IDs ({len(ids)}): {', '.join(ids[:8])}" + (' ...' if len(ids) > 8 else ''))
        if not items:
            # Fallback: count tags
            tags = re.findall(r'<(\w+)', content)
            unique = list(dict.fromkeys(tags))[:10]
            if unique:
                items.append(f"Elements: {', '.join(unique)}")

    elif ext in ('.css', '.scss', '.sass'):
        # Class and ID selectors
        selectors = re.findall(r'([.#][\w\-]+)\s*(?:,|\{)', content)
        unique_sel = list(dict.fromkeys(selectors))
        if unique_sel:
            items.append(f"Selectors ({len(unique_sel)}): {', '.join(unique_sel[:12])}" + (' ...' if len(unique_sel) > 12 else ''))
        # Element selectors (body, div, h1 etc.)
        el_sel = re.findall(r'^([a-z][\w\-]*)[\s,]*\{', content, re.MULTILINE)
        if el_sel:
            unique_el = list(dict.fromkeys(el_sel))
            items.append(f"Elements: {', '.join(unique_el[:10])}")
        media = re.findall(r'@media\s+([^{]+)\{', content)
        if media:
            items.append(f"Media queries: {len(media)}")
        if not items:
            rule_count = len(re.findall(r'\{', content))
            items.append(f"Rules: {rule_count}")

    elif ext == '.csv':
        first_line = content.split('\n')[0].strip()
        if first_line:
            cols = [c.strip().strip('"') for c in first_line.split(',')]
            items.append(f"Columns ({len(cols)}): {', '.join(cols[:10])}" + (' ...' if len(cols) > 10 else ''))
        row_count = max(0, len([l for l in content.split('\n') if l.strip()]) - 1)
        if row_count > 0:
            items.append(f"Rows: {row_count}")

    elif ext in ('.yaml', '.yml'):
        top_keys = re.findall(r'^(\w[\w\-]*):', content, re.MULTILINE)
        if top_keys:
            items.append(f"Keys: {', '.join(dict.fromkeys(top_keys))}")

    elif ext == '.md':
        headings = re.findall(r'^#{1,3}\s+(.+)', content, re.MULTILINE)
        if headings:
            items.append(f"Sections: {', '.join(headings[:6])}" + (' ...' if len(headings) > 6 else ''))

    elif ext in ('.env',):
        keys = re.findall(r'^([A-Z_][A-Z0-9_]*)=', content, re.MULTILINE)
        if keys:
            items.append(f"Variables: {', '.join(keys)}")

    return items


def parse_project(repo_path: str) -> dict:
    """Walk all files in repo_path and aggregate structure.

    Returns:
      {
        files:         list of {rel_path, classes, functions, imports, error, is_code}
        all_files_list: sorted list of all non-binary relative paths
        all_classes:   list of {name, bases, lineno, methods, file}
        all_functions: list of {name, args, returns, lineno, file}
        total_files:   int  (code files with detected structure)
        total_all:     int  (every non-binary file)
        total_classes: int,
        total_methods: int,
        total_functions: int,
      }
    """
    root = pathlib.Path(repo_path).resolve()
    code_files = []
    all_classes = []
    all_functions = []
    all_files_list = []
    file_summaries = {}  # rel_path -> list of summary strings for non-code files

    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        if path.suffix.lower() in _BINARY_EXTENSIONS:
            continue
        parts = set(path.relative_to(root).parts)
        if parts & _PROJECT_IGNORE:
            continue
        rel = path.relative_to(root).as_posix()
        all_files_list.append(rel)

        try:
            content = path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue

        ext = path.suffix.lower()
        if ext not in _CODE_EXTS:
            # Data/markup/config file — extract summary info
            summary = _parse_file_summary(content, path.name)
            if summary:
                file_summaries[rel] = summary
            continue

        structure = parse_structure(content, path.name)
        if not structure['supported']:
            continue
        if not structure['classes'] and not structure['functions']:
            continue

        file_entry = {
            'rel_path': rel,
            'classes': structure['classes'],
            'functions': structure['functions'],
            'imports': structure.get('imports', []),
            'error': structure['error'],
        }
        code_files.append(file_entry)

        for cls in structure['classes']:
            all_classes.append({**cls, 'file': rel})
        for fn in structure['functions']:
            all_functions.append({**fn, 'file': rel})

    total_methods = sum(len(c['methods']) for c in all_classes)

    return {
        'files': code_files,
        'all_files_list': all_files_list,
        'file_summaries': file_summaries,
        'all_classes': all_classes,
        'all_functions': all_functions,
        'total_files': len(code_files),
        'total_all': len(all_files_list),
        'total_classes': len(all_classes),
        'total_methods': total_methods,
        'total_functions': len(all_functions),
    }


def _build_inheritance_map(all_classes: list) -> dict:
    """Group classes by their base classes for the inheritance tree section.

    Returns {base_name: [child_class_dict, ...]}
    Only includes bases that have at least one child in the project.
    """
    known_names = {c['name'] for c in all_classes}
    tree: dict = {}
    for cls in all_classes:
        for base in cls['bases']:
            # Use only the short name (last segment) for display
            short_base = base.split('.')[-1]
            tree.setdefault(short_base, []).append(cls)
    return tree


def _wrap_names(names: list, prefix: str, max_width: int = 72) -> list:
    """Wrap a list of names into multiple lines.

    First line starts with `prefix`. Continuation lines are indented to
    align their first character under the first name on the first line.
    Items are comma-separated; no trailing comma on the last line.
    """
    if not names:
        return []
    indent = ' ' * len(prefix)
    result_lines = []
    current = prefix
    for i, name in enumerate(names):
        separator = ', ' if i < len(names) - 1 else ''
        token = name + separator
        # If adding this token would exceed max_width, flush and start new line
        if current != prefix and len(current) + len(token) > max_width:
            result_lines.append(current.rstrip(', '))
            current = indent + token
        else:
            current += token
    if current.strip():
        result_lines.append(current.rstrip(', '))
    return result_lines


def format_project_blueprint(project: dict, project_name: str) -> list:
    """Render a parse_project() result as plain-text lines for the results panel."""
    lines = []
    lines.append(f"PROJECT: {project_name}")
    lines.append(
        f"Files: {project['total_all']}  •  "
        f"Code: {project['total_files']}  •  "
        f"{project['total_classes']} class(es)  •  "
        f"{project['total_methods']} method(s)  •  "
        f"{project['total_functions']} function(s)"
    )
    lines.append("")

    # Build lookups
    code_map = {fe['rel_path']: fe for fe in project['files']}
    file_summaries = project.get('file_summaries', {})

    # Group all files by their top-level directory
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for rel in project.get('all_files_list', []):
        parts = rel.split('/')
        folder = parts[0] if len(parts) > 1 else '.'
        groups[folder].append(rel)

    for folder in sorted(groups.keys()):
        folder_label = folder if folder != '.' else project_name
        lines.append(f"── {folder_label}/ ──")
        for rel in groups[folder]:
            filename = rel.split('/')[-1]
            lines.append(f"  {filename}")

            if rel in code_map:
                # Code file with detected structure
                fe = code_map[rel]
                classes = fe['classes']
                functions = fe['functions']
                error = fe.get('error')

                if error:
                    lines.append(f"    ! Parse error: {error}")
                    continue

                for cls in classes:
                    bases_str = f" [inherits: {', '.join(cls['bases'])}]" if cls['bases'] else ""
                    lines.append(f"    CLASS {cls['name']}{bases_str}  [line {cls['lineno']}]")
                    methods = cls['methods']
                    if not methods:
                        lines.append("      └── (no methods)")
                    elif len(methods) <= 5:
                        for i, m in enumerate(methods):
                            connector = "└──" if i == len(methods) - 1 else "├──"
                            prefix = "async " if m['is_async'] else ""
                            lines.append(f"      {connector} {prefix}{m['name']}({m['args']}){m['returns']}  [line {m['lineno']}]")
                    else:
                        for m in methods[:4]:
                            prefix = "async " if m['is_async'] else ""
                            lines.append(f"      ├── {prefix}{m['name']}({m['args']}){m['returns']}  [line {m['lineno']}]")
                        lines.append(f"      └── ... and {len(methods) - 4} more method(s)")

                if functions:
                    names = [f['name'] for f in functions]
                    lines.extend(_wrap_names(names, prefix="    Functions: ", max_width=72))

            elif rel in file_summaries:
                # Non-code file with parsed summary
                for item in file_summaries[rel]:
                    lines.append(f"    {item}")

        lines.append("")

    # Inheritance map
    inh_map = _build_inheritance_map(project['all_classes'])
    if inh_map:
        lines.append("── INHERITANCE MAP ──")
        for base, children in sorted(inh_map.items()):
            lines.append(f"  {base}")
            for i, child in enumerate(children):
                connector = "└──" if i == len(children) - 1 else "├──"
                lines.append(f"  {connector} {child['name']}  ({child['file']})")
        lines.append("")

    return lines


def format_blueprint(structure: dict, filename: str) -> list:
    """Render a parse_structure() result as a list of plain-text lines."""
    lines = []

    lang = structure.get('language') or pathlib.Path(filename).suffix.lstrip('.').upper() or 'Unknown'

    if not structure['supported']:
        lines.append(f"Language: {lang} — sending source to Copilot for structural analysis.")
        return lines

    if structure['error']:
        lines.append(f"Parse error: {structure['error']}")
        lines.append("Copilot will attempt structural analysis on the raw file.")
        return lines

    n_classes = len(structure['classes'])
    n_methods = sum(len(c['methods']) for c in structure['classes'])
    n_funcs = len(structure['functions'])
    lines.append(f"Language: {lang}  •  {n_classes} class(es)  •  {n_methods} method(s)  •  {n_funcs} function(s)")
    lines.append("")

    if structure['imports']:
        lines.append("IMPORTS")
        for i, imp in enumerate(structure['imports']):
            connector = "└──" if i == len(structure['imports']) - 1 else "├──"
            lines.append(f"  {connector} {imp}")
        lines.append("")

    for cls in structure['classes']:
        bases_str = f"  (inherits: {', '.join(cls['bases'])})" if cls['bases'] else "  (no base class)"
        lines.append(f"CLASS {cls['name']}{bases_str}  [line {cls['lineno']}]")
        for i, m in enumerate(cls['methods']):
            connector = "└──" if i == len(cls['methods']) - 1 else "├──"
            prefix = "async " if m['is_async'] else ""
            lines.append(f"  {connector} {prefix}{m['name']}({m['args']}){m['returns']}  [line {m['lineno']}]")
        if not cls['methods']:
            lines.append("  └── (no methods)")
        lines.append("")

    if structure['functions']:
        lines.append("MODULE-LEVEL FUNCTIONS")
        for i, fn in enumerate(structure['functions']):
            connector = "└──" if i == len(structure['functions']) - 1 else "├──"
            prefix = "async " if fn['is_async'] else ""
            lines.append(f"  {connector} {prefix}{fn['name']}({fn['args']}){fn['returns']}  [line {fn['lineno']}]")

    return lines


def get_file_info(file_path):
    """Get processed metadata about a file"""
    path = pathlib.Path(file_path)
    
    if not path.exists():
        return None
    
    stat = path.stat()
    return {
        'name': path.name,
        'path': str(path),
        'size_raw': stat.st_size,
        'size_display': format_size(stat.st_size),
        'extension': path.suffix,
    }
