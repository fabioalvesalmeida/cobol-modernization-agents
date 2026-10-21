"""Deterministic static analysis of fixed-format COBOL.

The AI agents never read raw COBOL blindly: they call these functions through the
MCP server so every extracted fact (field layout, paragraph, computation, file
operation) is reproducible and traceable to a source line.
"""
from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

# ----------------------------------------------------------------- source

@dataclass
class SourceLine:
    number: int          # 1-based line number in the file
    indicator: str       # column 7
    area_a: bool         # code starts in columns 8-11
    text: str            # columns 8-72, right-stripped


def read_source(path: str | Path) -> list[SourceLine]:
    """Read a fixed-format COBOL file, dropping comment lines and sequence areas."""
    out: list[SourceLine] = []
    for i, raw in enumerate(Path(path).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        has_tab = "\t" in raw
        raw = raw.rstrip("\n").expandtabs(4 if has_tab else 8)
        indicator = raw[6] if len(raw) > 6 else " "
        if indicator in "*/":
            continue
        # Tabs are not valid in mainframe sources; files edited off-host may contain them,
        # so we do not truncate at column 72 in that case.
        code = (raw[7:] if has_tab else raw[7:72]) if len(raw) > 7 else ""
        if not code.strip():
            continue
        area_a = bool(code[:4].strip())
        out.append(SourceLine(i, indicator, area_a, code.rstrip()))
    return out


def _statements(lines: list[SourceLine]) -> list[tuple[int, str]]:
    """Join source into period-terminated statements: [(first_line, text)]."""
    stmts, buf, start = [], [], None
    for ln in lines:
        text = ln.text.strip()
        if ln.indicator == "-" and buf:          # continuation line
            buf[-1] = buf[-1] + text.lstrip("'\"")
        else:
            buf.append(text)
        start = start or ln.number
        if re.search(r"\.\s*$", text):
            stmts.append((start, " ".join(buf)))
            buf, start = [], None
    if buf:
        stmts.append((start, " ".join(buf)))
    return stmts

# ----------------------------------------------------------------- copybooks / data items

_PIC_RE = re.compile(r"\bPIC(?:TURE)?\s+(?:IS\s+)?(\S+)", re.I)
_OCCURS_RE = re.compile(r"\bOCCURS\s+(\d+)", re.I)
_REDEFINES_RE = re.compile(r"\bREDEFINES\s+([\w-]+)", re.I)
_USAGE_RE = re.compile(r"\b(COMP-3|COMPUTATIONAL-3|PACKED-DECIMAL|COMP-5|COMP-4|COMP|COMPUTATIONAL|BINARY)\b", re.I)


def _expand_pic(pic: str) -> str:
    pic = pic.rstrip(".").upper()
    return re.sub(r"(.)\((\d+)\)", lambda m: m.group(1) * int(m.group(2)), pic)


@dataclass
class Field:
    level: int
    name: str
    pic: str | None = None
    usage: str = "DISPLAY"
    occurs: int = 1
    redefines: str | None = None
    kind: str = "group"          # group | alphanumeric | numeric
    signed: bool = False
    digits: int = 0
    scale: int = 0
    length: int = 0              # bytes for one occurrence
    offset: int = 0              # bytes from the 01-level start
    java_type: str | None = None
    line: int = 0
    children: list["Field"] = field(default_factory=list)


def _elementary(f: Field) -> None:
    pic = _expand_pic(f.pic or "")
    f.signed = pic.startswith("S")
    if re.fullmatch(r"S?[9V]+P*", pic) or re.fullmatch(r"S?9*V?9*", pic):
        f.kind = "numeric"
        int_part, _, dec_part = pic.lstrip("S").partition("V")
        f.digits = int_part.count("9") + dec_part.count("9")
        f.scale = dec_part.count("9")
        u = f.usage.upper()
        if u in ("COMP-3", "COMPUTATIONAL-3", "PACKED-DECIMAL"):
            f.length = math.ceil((f.digits + 1) / 2)
        elif u in ("COMP", "COMPUTATIONAL", "BINARY", "COMP-4", "COMP-5"):
            f.length = 2 if f.digits <= 4 else 4 if f.digits <= 9 else 8
        else:
            f.length = f.digits
        if f.scale:
            f.java_type = "java.math.BigDecimal"
        else:
            f.java_type = "int" if f.digits <= 9 else "long" if f.digits <= 18 else "java.math.BigInteger"
    else:
        f.kind = "alphanumeric"
        f.length = len(pic)
        f.java_type = "String"


def parse_data_items(lines: list[SourceLine]) -> list[Field]:
    """Parse data description entries into a tree of 01-level records with offsets."""
    roots: list[Field] = []
    stack: list[Field] = []
    for line_no, stmt in _statements(lines):
        m = re.match(r"^(\d{1,2})\s+([\w-]+)?(.*)$", stmt.strip())
        if not m:
            continue
        level = int(m.group(1))
        if level in (66, 77, 88) and level != 77:
            continue                                  # 88 = condition names, 66 = RENAMES
        name = (m.group(2) or "FILLER").upper()
        rest = m.group(3)
        f = Field(level=level if level != 77 else 1, name=name, line=line_no)
        if (pm := _PIC_RE.search(rest)):
            f.pic = pm.group(1).rstrip(".")
        if (om := _OCCURS_RE.search(rest)):
            f.occurs = int(om.group(1))
        if (rm := _REDEFINES_RE.search(rest)):
            f.redefines = rm.group(1).upper()
        if (um := _USAGE_RE.search(rest)):
            f.usage = um.group(1).upper()
        while stack and stack[-1].level >= f.level:
            stack.pop()
        if stack:
            if stack[-1].usage != "DISPLAY" and f.usage == "DISPLAY":
                f.usage = stack[-1].usage                # group USAGE applies to children
            stack[-1].children.append(f)
        else:
            roots.append(f)
        stack.append(f)
    for r in roots:
        _layout(r, 0)
    return roots


def _layout(f: Field, offset: int) -> int:
    """Assign offsets/lengths; returns total bytes including OCCURS."""
    f.offset = offset
    if f.pic:
        _elementary(f)
    else:
        pos, by_name = offset, {}
        for c in f.children:
            start = by_name[c.redefines].offset if c.redefines in by_name else pos
            size = _layout(c, start)
            by_name[c.name] = c
            if not c.redefines:
                pos = start + size
        f.length = pos - offset
    return f.length * f.occurs


def flatten(fields: list[Field]) -> list[dict]:
    out = []
    def walk(f: Field, path: str):
        p = f"{path}.{f.name}" if path else f.name
        d = {k: v for k, v in asdict(f).items() if k != "children"}
        d["path"] = p
        out.append(d)
        for c in f.children:
            walk(c, p)
    for f in fields:
        walk(f, "")
    return out


def parse_copybook(path: str | Path) -> list[dict]:
    return flatten(parse_data_items(read_source(path)))

# ----------------------------------------------------------------- program structure

_COMPUTE_VERBS = ("COMPUTE", "ADD", "SUBTRACT", "MULTIPLY", "DIVIDE")
_FILE_VERBS = ("OPEN", "CLOSE", "READ", "WRITE", "REWRITE", "DELETE", "START")


def _division_bounds(lines: list[SourceLine]) -> dict[str, int]:
    bounds = {}
    for idx, ln in enumerate(lines):
        m = re.match(r"\s*(IDENTIFICATION|ID|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION", ln.text, re.I)
        if m:
            bounds[m.group(1).upper().replace("ID", "IDENTIFICATION") if m.group(1).upper() == "ID" else m.group(1).upper()] = idx
    return bounds


def program_structure(path: str | Path) -> dict:
    lines = read_source(path)
    b = _division_bounds(lines)
    proc_start = b.get("PROCEDURE", len(lines))
    pid = None
    for ln in lines[: proc_start]:
        if (m := re.match(r"\s*PROGRAM-ID\.\s*([\w-]+)", ln.text, re.I)):
            pid = m.group(1).upper()
            break
    copybooks = sorted({m.group(1).upper().rstrip(".") for ln in lines
                        for m in [re.search(r"\bCOPY\s+([\w-]+)", ln.text, re.I)] if m})
    files = []
    for ln in lines[: proc_start]:
        if (m := re.search(r"\bSELECT\s+([\w-]+)\s+ASSIGN\s+TO\s+([\w-]+)", ln.text, re.I)):
            files.append({"name": m.group(1).upper(), "dd": m.group(2).upper(), "line": ln.number})

    paragraphs: list[dict] = []
    current = None
    prev_line = lines[proc_start].number if proc_start < len(lines) else 0
    for ln in lines[proc_start + 1:]:
        if current is None and not re.match(r"^([\w-]+)(\s+SECTION)?\.\s*$", ln.text.strip()):
            current = {"name": "(MAIN)", "start_line": ln.number, "end_line": ln.number,
                       "performs": [], "computations": [], "file_ops": [], "cics": []}
            paragraphs.append(current)
        m = re.match(r"^([\w-]+)(\s+SECTION)?\.\s*$", ln.text.strip())
        if ln.area_a and m and m.group(1).upper() not in ("EXIT", "GOBACK"):
            if current:
                current["end_line"] = prev_line
            current = {"name": m.group(1).upper(), "start_line": ln.number, "end_line": ln.number,
                       "performs": [], "computations": [], "file_ops": [], "cics": []}
            paragraphs.append(current)
        if current is not None and not (ln.area_a and m and m.group(1).upper() not in ("EXIT", "GOBACK")):
            t = ln.text.strip()
            u = t.upper()
            for pm in re.finditer(r"\bPERFORM\s+([\w-]+)", u):
                tgt = pm.group(1)
                if tgt not in ("UNTIL", "VARYING", "WITH", "TEST") and tgt not in current["performs"]:
                    current["performs"].append(tgt)
            first = u.split()[0] if u.split() else ""
            if first in _COMPUTE_VERBS:
                current["computations"].append({"line": ln.number, "text": t})
            elif first in _FILE_VERBS:
                current["file_ops"].append({"line": ln.number, "text": t})
            if "EXEC CICS" in u:
                current["cics"].append({"line": ln.number, "text": t})
        prev_line = ln.number
    if current:
        current["end_line"] = prev_line if lines else current["start_line"]
    kind = "online (CICS)" if any(p["cics"] for p in paragraphs) else "batch"
    return {
        "program_id": pid,
        "path": str(path),
        "kind": kind,
        "source_lines": len(lines),
        "copybooks": copybooks,
        "files": files,
        "paragraphs": paragraphs,
    }


def extract_paragraph(path: str | Path, name: str) -> dict:
    """Return the raw source of one paragraph (comments removed) with line numbers."""
    s = program_structure(path)
    p = next((p for p in s["paragraphs"] if p["name"] == name.upper()), None)
    if not p:
        return {"error": f"paragraph {name} not found", "available": [x["name"] for x in s["paragraphs"]]}
    src = [ln for ln in read_source(path) if p["start_line"] <= ln.number <= p["end_line"]]
    return {"name": p["name"], "start_line": p["start_line"], "end_line": p["end_line"],
            "source": "\n".join(f"{ln.number:>5} {ln.text}" for ln in src)}


def list_programs(root: str | Path) -> list[dict]:
    out = []
    for f in sorted(Path(root).rglob("*")):
        if f.suffix.lower() in (".cbl", ".cob") and f.is_file():
            try:
                s = program_structure(f)
                out.append({"program_id": s["program_id"], "path": str(f), "kind": s["kind"],
                            "source_lines": s["source_lines"], "paragraphs": len(s["paragraphs"]),
                            "computations": sum(len(p["computations"]) for p in s["paragraphs"]),
                            "copybooks": s["copybooks"]})
            except Exception as e:  # keep the inventory going
                out.append({"path": str(f), "error": str(e)})
    return out
