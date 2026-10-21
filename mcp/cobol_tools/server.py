"""cobol-tools MCP server: grounded COBOL facts for modernization agents."""
from __future__ import annotations

import json
from pathlib import Path

try:  # MCP Python SDK 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # SDK 1.x
    from mcp.server.fastmcp import FastMCP as _Server

from . import analysis as A

mcp = _Server("cobol-tools")
_SCHEMA = Path(__file__).resolve().parents[2] / "schemas" / "business-rule-card.schema.json"


@mcp.tool()
def list_programs(root: str) -> list[dict]:
    """Inventory every COBOL program under a directory: id, batch/online, size, paragraphs, computations, copybooks."""
    return A.list_programs(root)


@mcp.tool()
def program_structure(path: str) -> dict:
    """Paragraphs with line ranges, PERFORM call graph, computations, file I/O and CICS commands of one program."""
    return A.program_structure(path)


@mcp.tool()
def extract_paragraph(path: str, name: str) -> dict:
    """Source of one paragraph with line numbers. Use it to quote the exact lines a business rule comes from."""
    return A.extract_paragraph(path, name)


@mcp.tool()
def parse_copybook(path: str) -> list[dict]:
    """Field layout of a copybook: level, PIC, numeric digits/scale, byte length, offset and suggested Java type."""
    return A.parse_copybook(path)


@mcp.tool()
def validate_rule_card(card: dict) -> dict:
    """Validate a Business Rule Card against the JSON schema and check that every rule cites source lines."""
    errors = []
    try:
        import jsonschema
        schema = json.loads(_SCHEMA.read_text())
        v = jsonschema.Draft202012Validator(schema)
        errors = [f"{'/'.join(map(str, e.path))}: {e.message}" for e in v.iter_errors(card)]
    except ImportError:
        errors.append("jsonschema not installed: structural validation skipped")
    for i, rule in enumerate(card.get("rules", [])):
        if not rule.get("source", {}).get("lines"):
            errors.append(f"rules/{i}: no source lines cited")
        if rule.get("status") == "approved" and not rule.get("reviewed_by"):
            errors.append(f"rules/{i}: approved without reviewer")
    return {"valid": not errors, "errors": errors}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
