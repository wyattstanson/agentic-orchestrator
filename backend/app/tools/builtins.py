"""Real, functional built-in tools. No network is required except http_get.

file_read / file_write / python_exec are confined to the configured workspace.
"""

from __future__ import annotations

import ast
import operator
import subprocess
import sys
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.models.enums import SpecialistRole
from app.models.tools import ToolSpec

from .registry import ToolRegistry


def _safe_path(rel: str) -> Path:
    root = get_settings().workspace_path
    target = (root / rel).resolve()
    if root not in target.parents and target != root:
        raise ValueError("Path escapes the tool workspace")
    return target


# -- file I/O --------------------------------------------------------------
def _file_write(args: dict[str, Any]) -> str:
    path = _safe_path(args["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(args["content"]), encoding="utf-8")
    return f"Wrote {len(str(args['content']))} chars to {args['path']}"


def _file_read(args: dict[str, Any]) -> str:
    return _safe_path(args["path"]).read_text(encoding="utf-8")


# -- calculator (safe arithmetic) ------------------------------------------
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos, ast.FloorDiv: operator.floordiv,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Unsupported expression")


def _calculator(args: dict[str, Any]) -> float:
    tree = ast.parse(str(args["expression"]), mode="eval")
    return _eval_node(tree.body)


# -- sandboxed code execution ----------------------------------------------
def _python_exec(args: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    proc = subprocess.run(
        [sys.executable, "-I", "-c", str(args["code"])],
        capture_output=True, text=True, timeout=settings.code_exec_timeout,
        cwd=settings.workspace_path,
    )
    return {
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-2000:],
        "returncode": proc.returncode,
    }


# -- http get --------------------------------------------------------------
def _http_get(args: dict[str, Any]) -> dict[str, Any]:
    import requests

    resp = requests.get(str(args["url"]), timeout=15)
    return {
        "status": resp.status_code,
        "content_type": resp.headers.get("content-type", ""),
        "body": resp.text[:6000],
    }


# -- web search (keyless, DuckDuckGo instant-answer API) -------------------
def _web_search(args: dict[str, Any]) -> dict[str, Any]:
    import requests

    query = str(args["query"])
    resp = requests.get(
        "https://api.duckduckgo.com/",
        params={"q": query, "format": "json", "no_html": 1, "no_redirect": 1},
        timeout=15,
        headers={"User-Agent": "orchestrator/0.1"},
    )
    data = resp.json()
    results: list[dict[str, str]] = []
    if data.get("AbstractText"):
        results.append(
            {
                "title": data.get("Heading", query),
                "snippet": data["AbstractText"],
                "url": data.get("AbstractURL", ""),
            }
        )
    for topic in data.get("RelatedTopics", []):
        if isinstance(topic, dict) and topic.get("Text"):
            results.append(
                {
                    "title": topic.get("Text", "")[:80],
                    "snippet": topic.get("Text", ""),
                    "url": topic.get("FirstURL", ""),
                }
            )
        if len(results) >= 6:
            break
    return {"query": query, "results": results}


# -- database query (local SQLite scratch db in the workspace) -------------
def _db_query(args: dict[str, Any]) -> dict[str, Any]:
    import sqlite3

    db_path = get_settings().workspace_path / "orchestrator.db"
    con = sqlite3.connect(db_path)
    try:
        cur = con.execute(str(args["sql"]))
        if cur.description:  # a SELECT-like statement
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchmany(200)]
            con.commit()
            return {"columns": cols, "rows": rows, "rowcount": len(rows)}
        con.commit()
        return {"rowcount": cur.rowcount}
    finally:
        con.close()


def register_builtins(registry: ToolRegistry) -> None:
    registry.register(
        ToolSpec(
            name="file_write",
            description="Write text to a file inside the workspace.",
            input_schema={"path": "string", "content": "string"},
            allowed_specialists=[SpecialistRole.WRITING, SpecialistRole.DATA, SpecialistRole.CODE],
        ),
        _file_write,
    )
    registry.register(
        ToolSpec(
            name="file_read",
            description="Read a text file from the workspace.",
            input_schema={"path": "string"},
        ),
        _file_read,
    )
    registry.register(
        ToolSpec(
            name="calculator",
            description="Evaluate a numeric arithmetic expression.",
            input_schema={"expression": "string"},
        ),
        _calculator,
    )
    registry.register(
        ToolSpec(
            name="python_exec",
            description="Run a short Python snippet in an isolated subprocess; returns stdout/stderr.",
            input_schema={"code": "string"},
            allowed_specialists=[SpecialistRole.CODE, SpecialistRole.DATA],
            rate_limit_per_min=20,
        ),
        _python_exec,
    )
    registry.register(
        ToolSpec(
            name="http_get",
            description="HTTP GET a URL and return status and truncated body.",
            input_schema={"url": "string"},
            allowed_specialists=[SpecialistRole.RESEARCH, SpecialistRole.DATA],
            rate_limit_per_min=30,
        ),
        _http_get,
    )
    registry.register(
        ToolSpec(
            name="web_search",
            description="Search the web (keyless) and return titles, snippets, and URLs.",
            input_schema={"query": "string"},
            allowed_specialists=[SpecialistRole.RESEARCH, SpecialistRole.DATA],
            rate_limit_per_min=20,
        ),
        _web_search,
    )
    registry.register(
        ToolSpec(
            name="db_query",
            description="Run SQL against a local SQLite database in the workspace.",
            input_schema={"sql": "string"},
            allowed_specialists=[SpecialistRole.DATA, SpecialistRole.CODE],
            rate_limit_per_min=40,
        ),
        _db_query,
    )


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    register_builtins(registry)
    return registry
