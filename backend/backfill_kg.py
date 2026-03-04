"""
One-time backfill: rebuild knowledge_graph_data for existing analyses
that completed before the field was added to the DB save.
"""
import asyncio
import json
import sqlite3
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


def build_simple_kg(claims_raw, fact_raw, source_url=None):
    """Rebuild a KG from stored JSON without calling Neo4j."""
    nodes, edges = [], []
    conflicts = 0
    verified = 0

    claims = claims_raw if isinstance(claims_raw, list) else []
    fact_results = fact_raw if isinstance(fact_raw, list) else []

    # Claim nodes
    for i, claim in enumerate(claims):
        node_id = f"claim_{i}"
        text = claim.get("claim_text", claim.get("text", "Claim")) if isinstance(claim, dict) else str(claim)
        nodes.append({"id": node_id, "label": text[:60], "type": "Claim", "color": "#00d2ff"})

    # Fact / verdict nodes
    for i, fact in enumerate(fact_results):
        if not isinstance(fact, dict):
            continue
        verdict = fact.get("verdict", "UNVERIFIABLE")
        if verdict == "SUPPORTED":
            node_type, color = "VerifiedFact", "#00e5a0"
            verified += 1
        elif verdict == "REFUTED":
            node_type, color = "DisputedFact", "#ff3a5c"
            conflicts += 1
        else:
            node_type, color = "UnverifiedFact", "#ffb830"

        fact_node_id = f"fact_{i}"
        evidence = fact.get("evidence", "")
        nodes.append({
            "id": fact_node_id,
            "label": f"{verdict}: {str(evidence)[:50]}",
            "type": node_type,
            "color": color,
        })
        claim_ref = f"claim_{i}" if i < len(claims) else (f"claim_0" if claims else None)
        if claim_ref:
            edges.append({"source": claim_ref, "target": fact_node_id, "label": "verified_as"})

        # Source nodes
        for j, src in enumerate(fact.get("sources", []) or []):
            if not isinstance(src, dict):
                continue
            src_node_id = f"src_{i}_{j}"
            nodes.append({
                "id": src_node_id,
                "label": src.get("title", src.get("publisher", "Source"))[:40],
                "type": "Source",
                "color": "#ffb830",
            })
            edges.append({"source": fact_node_id, "target": src_node_id, "label": "sourced_from"})

    # Source domain node
    if source_url:
        try:
            from urllib.parse import urlparse
            domain = urlparse(source_url).netloc
            if domain:
                nodes.append({"id": "domain_0", "label": domain, "type": "Source", "color": "#ffb830"})
                for i in range(len(claims)):
                    edges.append({"source": f"claim_{i}", "target": "domain_0", "label": "published_by"})
        except Exception:
            pass

    return {"nodes": nodes, "edges": edges, "conflicts": conflicts, "verified": verified}


def backfill():
    db_path = Path(__file__).parent / "veritruth.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, detected_claims, fact_verification_results, source_url "
        "FROM analyses WHERE status='COMPLETED' AND knowledge_graph_data IS NULL"
    ).fetchall()

    updated = 0
    for row in rows:
        try:
            claims = json.loads(row["detected_claims"]) if row["detected_claims"] else []
            facts = json.loads(row["fact_verification_results"]) if row["fact_verification_results"] else []
            kg = build_simple_kg(claims, facts, row["source_url"])
            conn.execute(
                "UPDATE analyses SET knowledge_graph_data=? WHERE id=?",
                (json.dumps(kg), row["id"]),
            )
            print(f"  Backfilled {row['id'][:8]}... nodes={len(kg['nodes'])} edges={len(kg['edges'])}")
            updated += 1
        except Exception as e:
            print(f"  SKIP {row['id'][:8]}...: {e}")

    conn.commit()
    conn.close()
    print(f"Done — updated {updated} analyses.")


if __name__ == "__main__":
    backfill()
