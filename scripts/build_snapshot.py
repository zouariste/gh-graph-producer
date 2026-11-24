#!/usr/bin/env python3
"""Producer: extract a code-only graph and write a publication snapshot (graph.json + manifest.json)
that satisfies the consumer's validate_snapshot contract."""
import argparse, hashlib, json, subprocess
from pathlib import Path
import networkx as nx

GRAPHIFY_VERSION = "0.9.118"

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="src", help="code dir to extract (relative to CWD)")
    ap.add_argument("--repository", required=True, help="owner/repo, must match consumer registry")
    ap.add_argument("--source-commit", required=True, help="40-hex commit SHA (github.sha)")
    ap.add_argument("--graphify", default="graphify")
    ap.add_argument("--output", type=Path, default=Path("out"))
    args = ap.parse_args()

    # 1. Headless, no-LLM, code-only AST extraction.
    subprocess.run([args.graphify, "update", args.source, "--no-cluster", "--force"], check=True)
    raw = json.loads((Path(args.source) / "graphify-out" / "graph.json").read_bytes())

    # 2. Promote the raw extraction to a directed multigraph (the published contract).
    g = nx.MultiDiGraph()
    for node in raw["nodes"]:
        g.add_node(node["id"], **{k: v for k, v in node.items() if k != "id"})
    for edge in raw["links"]:
        g.add_edge(edge["source"], edge["target"],
                   **{k: v for k, v in edge.items() if k not in ("source", "target", "key")})
    g.graph["hyperedges"] = raw.get("hyperedges", [])
    data = nx.node_link_data(g, edges="links")

    # 3. Coverage: paths exactly as graphify reports them (relative to CWD).
    java = sorted(str(p) for p in Path(args.source).rglob("*.java"))
    represented = sorted({n["source_file"] for n in data["nodes"] if n.get("source_file")})
    missing = [f for f in java if f not in represented]
    fingerprint = hashlib.sha256()
    for rel in java:
        fingerprint.update(rel.encode()); fingerprint.update(b"\0")
        fingerprint.update(Path(rel).read_bytes()); fingerprint.update(b"\0")

    # 4. Write graph first, hash its exact bytes, then the manifest (consumers reject mismatches).
    args.output.mkdir(parents=True, exist_ok=True)
    graph_bytes = canonical(data).encode()
    (args.output / "graph.json").write_bytes(graph_bytes)
    manifest = {
        "schema_version": 1, "repository": args.repository,
        "graphify_version": GRAPHIFY_VERSION, "scope": "code-only",
        "source_commit": args.source_commit, "source_fingerprint": fingerprint.hexdigest(),
        "nodes": len(data["nodes"]), "links": len(data["links"]),
        "graph_sha256": hashlib.sha256(graph_bytes).hexdigest(),
        "coverage": {"files": len(java), "represented": len(represented), "missing": missing},
    }
    (args.output / "manifest.json").write_text(canonical(manifest))
    print(f"Snapshot: {manifest['nodes']} nodes, {manifest['links']} links, "
          f"coverage {len(represented)}/{len(java)}")

if __name__ == "__main__":
    main()
