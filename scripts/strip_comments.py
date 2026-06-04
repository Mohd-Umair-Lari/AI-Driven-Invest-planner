#!/usr/bin/env python3
import pathlib, re, sys, tokenize, io, os

# Define extensions and comment stripping strategies
PY_EXT = {'.py'}
JS_EXT = {'.js', '.ts', '.jsx', '.tsx'}
HTML_EXT = {'.html'}
CSS_EXT = {'.css'}
OTHER_EXT = {'.java', '.c', '.cpp', '.h', '.cs', '.go', '.rb', '.php'}

def strip_python(source: str) -> str:
    """Remove comments (tokenize.COMMENT) but keep docstrings and strings."""
    out = []
    g = tokenize.generate_tokens(io.StringIO(source).readline)
    for toknum, tokval, _, _, _ in g:
        if toknum == tokenize.COMMENT:
            # replace comment with empty line to keep line numbers roughly same
            continue
        out.append(tokval)
    return ''.join(out)

def strip_generic(source: str, patterns) -> str:
    for pat in patterns:
        source = re.sub(pat, '', source, flags=re.MULTILINE|re.DOTALL)
    return source

def process_file(path: pathlib.Path):
    ext = path.suffix.lower()
    text = path.read_text(encoding='utf-8')
    original = text
    if ext in PY_EXT:
        new_text = strip_python(text)
    elif ext in JS_EXT:
        # Remove // comments and /* */ block comments
        patterns = [r'//.*?$' , r'/\*.*?\*/']
        new_text = strip_generic(text, patterns)
    elif ext in HTML_EXT:
        patterns = [r'<!--.*?-->', r'/\*.*?\*/']
        new_text = strip_generic(text, patterns)
    elif ext in CSS_EXT:
        patterns = [r'/\*.*?\*/']
        new_text = strip_generic(text, patterns)
    elif ext in OTHER_EXT:
        # generic // and /* */
        patterns = [r'//.*?$', r'/\*.*?\*/']
        new_text = strip_generic(text, patterns)
    else:
        return  # skip unknown types
    if new_text != original:
        # Write to a temp file first then replace
        tmp_path = path.with_suffix(path.suffix + '.tmp')
        tmp_path.write_text(new_text, encoding='utf-8')
        # Verify python files still compile
        if ext == '.py':
            import py_compile, traceback
            try:
                py_compile.compile(str(tmp_path), doraise=True)
            except Exception as e:
                print(f"[WARN] Skipping {path} due to compile error: {e}")
                tmp_path.unlink()
                return
        # Replace original
        path.write_text(new_text, encoding='utf-8')
        if tmp_path.exists():
            tmp_path.unlink()
        print(f"Stripped comments from {path}")

def main():
    root = pathlib.Path('.').resolve()
    for path in root.rglob('*'):
        if path.is_file() and path.suffix.lower() in {'.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.java', '.c', '.cpp', '.h', '.cs', '.go', '.rb', '.php'}:
            try:
                process_file(path)
            except Exception as exc:
                print(f"[ERROR] Failed processing {path}: {exc}")

if __name__ == '__main__':
    main()