# Convert Markdown text to paragraphs inside a python-docx Document
# Uses mistune for parsing, python-docx for rendering
import mistune

from logger import log


# Add markdown text into an existing python-docx Document
# Returns tuple (blocks_added, chars_written) or (0, 0) on failure
# chars_written is total length of paragraph text that was added
def append_markdown(document, markdown_text: str) -> tuple:
    if not markdown_text or not markdown_text.strip():
        return 0, 0
    try:
        md = mistune.create_markdown(renderer="ast")
        tokens = md(markdown_text)
    except Exception as e:
        log.exception("markdown_to_docx: parse error: %s", e)
        return 0, 0
    before_paras = len(document.paragraphs)
    added = 0
    for token in tokens:
        added += _render_block(document, token)
    new_paras = document.paragraphs[before_paras:]
    chars_written = sum(len(p.text) for p in new_paras)
    return added, chars_written


# Render a top-level block token into the document
# Returns number of paragraphs added
def _render_block(document, token: dict) -> int:
    ttype = token.get("type", "")
    if ttype == "heading":
        _render_heading(document, token)
        return 1
    if ttype == "paragraph":
        _render_paragraph(document, token)
        return 1
    if ttype == "block_code":
        _render_code(document, token)
        return 1
    if ttype == "list":
        return _render_list(document, token, 0)
    if ttype == "block_quote":
        _render_blockquote(document, token)
        return 1
    if ttype == "thematic_break":
        document.add_paragraph("----------")
        return 1
    if ttype == "table":
        _render_table(document, token)
        return 1
    # Unknown block type: dump children as text if any
    for child in token.get("children", []) or []:
        _render_block(document, child)
    return 1


# Render heading block
def _render_heading(document, token: dict) -> None:
    level = int(token.get("attrs", {}).get("level", 1))
    if level < 1:
        level = 1
    if level > 6:
        level = 6
    text = _inline_plain(token.get("children", []))
    try:
        document.add_heading(text, level=level)
    except Exception:
        document.add_paragraph(text)


# Render paragraph block with inline formatting
def _render_paragraph(document, token: dict) -> None:
    p = document.add_paragraph()
    _render_inline(p, token.get("children", []))


# Render code block with monospace font
def _render_code(document, token: dict) -> None:
    text = token.get("raw", "") or ""
    text = text.rstrip("\n")
    for line in text.split("\n"):
        p = document.add_paragraph()
        run = p.add_run(line)
        try:
            run.font.name = "Consolas"
        except Exception:
            pass


# Render block quote with indent
def _render_blockquote(document, token: dict) -> None:
    for child in token.get("children", []) or []:
        if child.get("type") == "paragraph":
            p = document.add_paragraph()
            try:
                p.paragraph_format.left_indent = 360000
            except Exception:
                pass
            _render_inline(p, child.get("children", []))


# Render list block recursively
def _render_list(document, token: dict, depth: int) -> int:
    ordered = bool(token.get("attrs", {}).get("ordered", False))
    style = "List Number" if ordered else "List Bullet"
    count = 0
    for item in token.get("children", []) or []:
        if item.get("type") != "list_item":
            continue
        first_para_done = False
        for child in item.get("children", []) or []:
            ctype = child.get("type")
            if ctype in ("paragraph", "block_text"):
                if not first_para_done:
                    p = document.add_paragraph(style=style)
                    try:
                        p.paragraph_format.left_indent = 360000 * (depth + 1)
                    except Exception:
                        pass
                    _render_inline(p, child.get("children", []))
                    first_para_done = True
                    count += 1
                else:
                    p = document.add_paragraph()
                    _render_inline(p, child.get("children", []))
                    count += 1
            elif ctype == "list":
                count += _render_list(document, child, depth + 1)
    return count


# Render inline tokens into a paragraph
def _render_inline(paragraph, children) -> None:
    for child in children or []:
        ttype = child.get("type", "")
        if ttype == "text":
            paragraph.add_run(child.get("raw", ""))
        elif ttype == "strong":
            run = paragraph.add_run(_inline_plain(child.get("children", [])))
            run.bold = True
        elif ttype == "emphasis":
            run = paragraph.add_run(_inline_plain(child.get("children", [])))
            run.italic = True
        elif ttype == "codespan":
            run = paragraph.add_run(child.get("raw", ""))
            try:
                run.font.name = "Consolas"
            except Exception:
                pass
        elif ttype == "link":
            run = paragraph.add_run(_inline_plain(child.get("children", [])))
            try:
                run.underline = True
            except Exception:
                pass
        elif ttype == "softbreak":
            paragraph.add_run(" ")
        elif ttype == "linebreak":
            paragraph.add_run("\n")
        elif ttype == "inline_html":
            paragraph.add_run(child.get("raw", ""))
        else:
            if child.get("children"):
                _render_inline(paragraph, child.get("children", []))


# Extract plain text from inline children
def _inline_plain(children) -> str:
    parts = []
    for child in children or []:
        ttype = child.get("type", "")
        if ttype == "text" or ttype == "codespan":
            parts.append(child.get("raw", ""))
        elif ttype == "softbreak":
            parts.append(" ")
        elif ttype == "linebreak":
            parts.append("\n")
        elif child.get("children"):
            parts.append(_inline_plain(child.get("children", [])))
    return "".join(parts)


# Render table block (basic, no styling)
def _render_table(document, token: dict) -> None:
    rows = []
    for child in token.get("children", []) or []:
        if child.get("type") != "table_body":
            continue
        for row in child.get("children", []) or []:
            if row.get("type") == "table_row":
                cells = []
                for cell in row.get("children", []) or []:
                    cells.append(_inline_plain(cell.get("children", [])))
                rows.append(cells)
    if not rows:
        return
    cols = max(len(r) for r in rows)
    try:
        table = document.add_table(rows=len(rows), cols=cols)
        table.style = "Table Grid"
        for ri, row in enumerate(rows):
            for ci in range(cols):
                text = row[ci] if ci < len(row) else ""
                table.cell(ri, ci).text = text
    except Exception as e:
        log.exception("markdown_to_docx: table error: %s", e)