# gh-graph-producer

Publishes a knowledge graph of this repo's code as a downloadable CI artifact.

On every push to `main`, GitHub Actions:

1. installs the pinned extractor (`graphifyy==0.9.118`),
2. builds a **code-only** graph from `src/` (no LLM, deterministic),
3. writes `out/graph.json` + `out/manifest.json` (a directed multigraph plus a
   manifest with the source commit, a source fingerprint, coverage, and a
   SHA-256 checksum),
4. uploads it as the artifact **`graphify-sample-lib-<commit-sha>`**.

A separate consumer repo discovers the latest successful run of this workflow,
downloads the artifact, re-validates it, and assembles it.

## Layout

| Path | Purpose |
|------|---------|
| `src/main/java/hello/` | the sample code that gets graphed |
| `scripts/build_snapshot.py` | extraction + manifest writer |
| `.github/workflows/knowledge-graph.yml` | the publish pipeline |

## Run it locally

```bash
python -m venv .venv-graphify
.venv-graphify/bin/python -m pip install -r requirements-graphify.txt
.venv-graphify/bin/python scripts/build_snapshot.py \
  --source src \
  --repository you/gh-graph-producer \
  --source-commit $(printf '%040d' 0 | tr 0 a) \
  --graphify .venv-graphify/bin/graphify \
  --output out
```

## Optional: notify the consumer automatically

Set the repo secret `CONSUMER_DISPATCH_TOKEN` (a token with `repo` access to the
consumer) and each publish pings the consumer to reassemble. Leave it unset and
the consumer just runs on its own schedule or on demand.

## Query this project's published graph

After a push publishes `graphify-sample-lib-<sha>`, query it directly.
`scripts/graph-query` resolves the latest successful run, downloads that artifact
**only when it changed**, verifies the checksum, caches it, then queries:

```bash
scripts/graph-query "how does Greeter work"
scripts/graph-query --explain "Greeter"
scripts/graph-query --path "App" "Greeter"
```

Needs `gh auth login -h github.com` once and a graphify binary (set `GRAPHIFY_BIN`,
or create `.venv-graphify` from `requirements-graphify.txt`, or `graphify` on PATH).

## Local graph & git hook

A pre-commit hook rebuilds the local code graph of `src/` and stages
`graphify-out/graph.json`, so the committed graph always matches the committed
source. Enable it once per clone:

```bash
git config core.hooksPath .githooks
```

The `graph` skill (`.claude/skills/graph`) routes a question to the local graph
(`graphify query`) or to `scripts/graph-query` for the published one.
