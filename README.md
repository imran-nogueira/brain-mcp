<picture><source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.png"><img alt="brain-mcp — A read-only MCP server giving Claude direct access to a personal Markdown knowledge base." src="assets/banner-light.png"></picture>

I keep a structured record of my projects and skills as plain Markdown files with YAML frontmatter. `brain-mcp` lets Claude (Claude Code, Claude Desktop, or any MCP client) query that record directly: search it, read a project or a skill, list and filter, get a summary.

- **FastMCP (Python)**, **stdio** transport, runs **locally**.
- **Read-only by design** — no tool writes to the knowledge base.
- **No embeddings, no vector database** — the base is a few dozen files; structured filters plus keyword search are enough, and anything more would be over-engineering at this size.
- **Always fresh** — files are re-read on every call, so an edit is visible immediately without restarting the server.

## Tools

| Tool | What it returns |
|---|---|
| `search_brain(query, kind?)` | Keyword search across projects, skills and contexts (name, category, stack, pitch, body). |
| `get_project(name)` | A project: context, world, portfolio tier, pitch, stack, status, period, repository. |
| `get_skill(name)` | A skill: level, confidence, category, the projects that prove it, related skills, derived world(s). |
| `list_projects(world?, tier?, context?)` | Filtered list of projects. |
| `list_skills(category?, level?, confidence?, world?)` | Filtered list of skills. |
| `get_view(name)` | Raw Markdown of a generated view (`cv`, `competences`, `epitech`, `perso`). |
| `brain_overview()` | Quick summary: counts per world, showcase projects, strongest skills. |

Every tool ships a detailed docstring (return schema and examples) that MCP clients display.

## Knowledge-base format

```
brain/
├── projets/       # one Markdown file per project
├── competences/   # one per skill
├── contextes/     # one per context (school, internship, personal…)
└── vues/          # generated views
```

Each file starts with YAML frontmatter (`type`, `nom`, `statut`, `stack`, `portfolio_tier`, `confidence`…) followed by a Markdown body. A project's *world* is derived from its context; a skill's worlds are derived from the projects that prove it.

## Install

```bash
git clone https://github.com/imran-nogueira/brain-mcp.git
cd brain-mcp
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Run

```bash
BRAIN_PATH=/path/to/your/brain .venv/bin/brain-mcp
```

The server speaks JSON-RPC over stdin, so it waits silently when launched by hand. To explore the tools interactively:

```bash
npx @modelcontextprotocol/inspector .venv/bin/brain-mcp
```

## Register it in Claude Code

```bash
claude mcp add brain -s user -e BRAIN_PATH="/path/to/your/brain" -- "/path/to/brain-mcp/.venv/bin/brain-mcp"
```

For other clients, use the standard `mcpServers` JSON entry:

```json
{
  "mcpServers": {
    "brain": {
      "command": "/path/to/brain-mcp/.venv/bin/brain-mcp",
      "env": { "BRAIN_PATH": "/path/to/your/brain" }
    }
  }
}
```

## Tests

```bash
.venv/bin/python -m pytest -v
```

27 tests run against a small, isolated, deterministic knowledge base built in fixtures. 5 more parser tests read a real entity and are skipped automatically when no knowledge base is mounted.

## Project layout

```
src/brain_mcp/
├── parser.py   # YAML frontmatter + Markdown body
├── brain.py    # loading, world derivation, search, filters — testable without MCP
└── server.py   # FastMCP: 7 tools, Pydantic models, stdio
tests/
```

## Limits (v1)

- Exact keyword search (case-insensitive substring), no fuzzy or semantic search.
- Read-only: no writing or validation of entities.

## License

MIT
