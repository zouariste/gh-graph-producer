---
name: graph
description: Query this project's code knowledge graph — the local committed graph for questions about the current source, or the exact CI-published graph via scripts/graph-query.
---

# Query the code graph

This project graphs its own `src/`. Two views:

## Local graph (committed, kept fresh on commit)

`graphify-out/graph.json` is rebuilt from `src/` and staged by the pre-commit
hook, so it always matches the committed source. Ask it directly:

```bash
.venv-graphify/bin/graphify query "how does Greeter work" --budget 2000
.venv-graphify/bin/graphify explain "Greeter"
.venv-graphify/bin/graphify path "App" "Greeter"
```

Use `GRAPHIFY_BIN` or `graphify` on PATH if there is no `.venv-graphify`.
Unstaged edits are not in the committed graph until you commit.

## Published graph (the CI artifact)

For the exact graph published by CI (pinned to a commit), use the wrapper — it
fetches the latest artifact only when it changed, verifies the checksum, caches
it, then queries:

```bash
scripts/graph-query "how does Greeter work"
scripts/graph-query --explain "Greeter"
```

## Notes

- Cite source file/line and the edge relation. A `contains`/`references` path is
  not automatically a runtime call chain.
- Start from real symbol names; use `--seed <id>` for a precise entry point.
