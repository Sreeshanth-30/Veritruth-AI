# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Knowledge Graph Service (Neo4j)
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def build_knowledge_graph(
    entities: list[dict],
    claims: list[dict],
    fact_results: list[dict],
    source_url: str | None = None,
) -> dict[str, Any]:
    """Build a knowledge graph from extracted entities, claims, and fact-check results.
    
    Stores in Neo4j and returns a D3.js-compatible node/edge structure.
    
    Returns:
        {
            "nodes": [{"id": "...", "label": "...", "type": "...", "color": "..."}],
            "edges": [{"source": "...", "target": "...", "label": "..."}],
            "conflicts": int,
            "verified": int,
        }
    """
    from app.core.database import get_neo4j_driver

    nodes = []
    edges = []
    conflicts = 0
    verified = 0

    # Create nodes from entities
    entity_ids = {}
    for i, ent in enumerate(entities):
        node_id = f"entity_{i}"
        entity_ids[ent["text"].lower()] = node_id
        nodes.append({
            "id": node_id,
            "label": ent["text"],
            "type": "Entity",
            "color": "#a0a0ff",
            "entity_type": ent["label"],
        })

    # Create claim nodes
    for i, claim in enumerate(claims):
        node_id = f"claim_{i}"
        nodes.append({
            "id": node_id,
            "label": claim["claim_text"][:60] + "...",
            "type": "Claim",
            "color": "#00d2ff",
            "full_text": claim["claim_text"],
        })

        # Link claims to mentioned entities
        for ent in claim.get("entities", []):
            ent_id = entity_ids.get(ent["text"].lower())
            if ent_id:
                edges.append({
                    "source": node_id,
                    "target": ent_id,
                    "label": "mentions",
                })

    # Create fact verification result nodes
    for i, fact in enumerate(fact_results):
        verdict = fact.get("verdict", "UNVERIFIABLE")

        if verdict == "SUPPORTED":
            node_type = "VerifiedFact"
            color = "#00e5a0"
            verified += 1
        elif verdict == "REFUTED":
            node_type = "DisputedFact"
            color = "#ff3a5c"
            conflicts += 1
        else:
            node_type = "UnverifiedFact"
            color = "#ffb830"

        fact_node_id = f"fact_{i}"
        nodes.append({
            "id": fact_node_id,
            "label": f"{verdict}: {fact.get('evidence', '')[:50]}...",
            "type": node_type,
            "color": color,
        })

        # Link fact to its claim
        edges.append({
            "source": f"claim_{i}" if i < len(claims) else f"claim_0",
            "target": fact_node_id,
            "label": "verified_as",
        })

        # Link to evidence sources
        for j, src in enumerate(fact.get("sources", [])):
            src_node_id = f"source_{i}_{j}"
            nodes.append({
                "id": src_node_id,
                "label": src.get("title", "Unknown Source")[:40],
                "type": "Source",
                "color": "#ffb830",
                "url": src.get("url", ""),
            })
            edges.append({
                "source": fact_node_id,
                "target": src_node_id,
                "label": "sourced_from",
            })

    # Add source domain node if URL provided
    if source_url:
        from urllib.parse import urlparse
        domain = urlparse(source_url).netloc
        source_node_id = "source_domain"
        nodes.append({
            "id": source_node_id,
            "label": domain,
            "type": "Source",
            "color": "#ffb830",
        })
        # Link all claims to source domain
        for i in range(len(claims)):
            edges.append({
                "source": f"claim_{i}",
                "target": source_node_id,
                "label": "published_by",
            })

    # Store in Neo4j
    try:
        driver = get_neo4j_driver()
        async with driver.session() as session:
            # Clear previous graph for this analysis
            await session.run("MATCH (n) DETACH DELETE n")

            # Create nodes
            for node in nodes:
                await session.run(
                    """
                    CREATE (n:Node {
                        id: $id,
                        label: $label,
                        type: $type,
                        color: $color
                    })
                    """,
                    id=node["id"],
                    label=node["label"],
                    type=node["type"],
                    color=node["color"],
                )

            # Create edges
            for edge in edges:
                await session.run(
                    """
                    MATCH (a:Node {id: $source}), (b:Node {id: $target})
                    CREATE (a)-[:RELATES {label: $label}]->(b)
                    """,
                    source=edge["source"],
                    target=edge["target"],
                    label=edge["label"],
                )

        logger.info(
            "Knowledge graph built: %d nodes, %d edges, %d conflicts, %d verified",
            len(nodes), len(edges), conflicts, verified,
        )
    except Exception as e:
        logger.warning("Neo4j graph storage failed (non-fatal): %s", e)

    return {
        "nodes": nodes,
        "edges": edges,
        "conflicts": conflicts,
        "verified": verified,
    }
