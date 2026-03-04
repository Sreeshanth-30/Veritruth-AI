"use client";

import React, { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import * as d3 from "d3";
import api from "@/lib/api";
import { cn } from "@/lib/utils";
import { Network, ZoomIn, ZoomOut, Maximize2, Info } from "lucide-react";
import type { KnowledgeGraphData, KnowledgeGraphNode, KnowledgeGraphEdge } from "@/lib/types";

export default function KnowledgeGraphPage() {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedNode, setSelectedNode] = useState<KnowledgeGraphNode | null>(null);

  // Fetch latest analysis knowledge graph data
  const { data: kgData } = useQuery<KnowledgeGraphData>({
    queryKey: ["knowledge-graph"],
    queryFn: async () => {
      // Get the latest completed analysis's knowledge graph
      const { data: list } = await api.get("/analysis", {
        params: { page: 1, page_size: 1 },
      });
      if (!list?.items?.length) return { nodes: [], edges: [], conflicts: 0, verified: 0 };
      const latestId = list.items[0].id;
      const { data: analysis } = await api.get(`/analysis/${latestId}`);
      return analysis.knowledge_graph_data || { nodes: [], edges: [], conflicts: 0, verified: 0 };
    },
  });

  useEffect(() => {
    if (!kgData?.nodes?.length || !svgRef.current || !containerRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight || 600;

    const g = svg
      .attr("width", width)
      .attr("height", height)
      .append("g");

    // Zoom
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 5])
      .on("zoom", (event) => g.attr("transform", event.transform));
    svg.call(zoom);

    // Simulation
    const sim = d3.forceSimulation(kgData.nodes as any)
      .force("link", d3.forceLink(kgData.edges as any).id((d: any) => d.id).distance(120))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(40));

    // Edges
    const link = g.selectAll(".link")
      .data(kgData.edges)
      .enter()
      .append("line")
      .attr("class", "link")
      .attr("stroke", "rgba(255,255,255,0.15)")
      .attr("stroke-width", 1.5);

    // Edge labels
    const linkLabel = g.selectAll(".link-label")
      .data(kgData.edges)
      .enter()
      .append("text")
      .attr("class", "link-label")
      .text((d: KnowledgeGraphEdge) => d.label)
      .attr("font-size", "9px")
      .attr("fill", "rgba(255,255,255,0.4)")
      .attr("text-anchor", "middle");

    // Nodes
    const node = g.selectAll(".node")
      .data(kgData.nodes)
      .enter()
      .append("circle")
      .attr("class", "node")
      .attr("r", (d: KnowledgeGraphNode) => {
        switch (d.type) {
          case "Claim": return 12;
          case "Source": return 10;
          case "VerifiedFact": return 14;
          case "DisputedFact": return 14;
          default: return 8;
        }
      })
      .attr("fill", (d: KnowledgeGraphNode) => d.color)
      .attr("stroke", "rgba(255,255,255,0.2)")
      .attr("stroke-width", 1.5)
      .style("cursor", "pointer")
      .on("click", (event: any, d: any) => {
        setSelectedNode(d as KnowledgeGraphNode);
      })
      .call(
        d3.drag<SVGCircleElement, any>()
          .on("start", (event: any, d: any) => {
            if (!event.active) sim.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event: any, d: any) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event: any, d: any) => {
            if (!event.active) sim.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }) as any
      );

    // Node labels
    const nodeLabel = g.selectAll(".node-label")
      .data(kgData.nodes)
      .enter()
      .append("text")
      .attr("class", "node-label")
      .text((d: KnowledgeGraphNode) => d.label.slice(0, 20))
      .attr("font-size", "10px")
      .attr("fill", "white")
      .attr("text-anchor", "middle")
      .attr("dy", -16);

    sim.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      linkLabel
        .attr("x", (d: any) => (d.source.x + d.target.x) / 2)
        .attr("y", (d: any) => (d.source.y + d.target.y) / 2);

      node
        .attr("cx", (d: any) => d.x)
        .attr("cy", (d: any) => d.y);

      nodeLabel
        .attr("x", (d: any) => d.x)
        .attr("y", (d: any) => d.y);
    });

    return () => { sim.stop(); };
  }, [kgData]);

  const nodeCount = kgData?.nodes?.length ?? 0;
  const edgeCount = kgData?.edges?.length ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold text-white">
          Knowledge Graph
        </h1>
        <p className="mt-1 text-dark-300">
          Interactive entity-relationship visualisation of your latest analysis.
        </p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4">
        <div className="glass-card text-center">
          <div className="font-heading text-2xl font-bold text-brand-primary">{nodeCount}</div>
          <div className="text-xs text-dark-400">Nodes</div>
        </div>
        <div className="glass-card text-center">
          <div className="font-heading text-2xl font-bold text-brand-secondary">{edgeCount}</div>
          <div className="text-xs text-dark-400">Edges</div>
        </div>
        <div className="glass-card text-center">
          <div className="font-heading text-2xl font-bold text-brand-accent">{kgData?.verified ?? 0}</div>
          <div className="text-xs text-dark-400">Verified</div>
        </div>
        <div className="glass-card text-center">
          <div className="font-heading text-2xl font-bold text-brand-danger">{kgData?.conflicts ?? 0}</div>
          <div className="text-xs text-dark-400">Conflicts</div>
        </div>
      </div>

      {/* Graph Canvas */}
      <div className="glass-card relative !p-0 overflow-hidden" style={{ height: "600px" }}>
        {nodeCount === 0 ? (
          <div className="flex h-full items-center justify-center text-dark-400">
            <div className="text-center">
              <Network className="mx-auto h-12 w-12 text-dark-500" />
              <p className="mt-4">No knowledge graph data available.</p>
              <p className="text-sm">Run an analysis first to generate a knowledge graph.</p>
            </div>
          </div>
        ) : (
          <div ref={containerRef} className="h-full w-full">
            <svg ref={svgRef} className="h-full w-full" />
          </div>
        )}

        {/* Legend */}
        <div className="absolute bottom-4 left-4 flex flex-wrap gap-3 rounded-lg bg-dark-900/90 px-4 py-2 backdrop-blur">
          {[
            { color: "#a0a0ff", label: "Entity" },
            { color: "#00d2ff", label: "Claim" },
            { color: "#00e5a0", label: "Verified" },
            { color: "#ff3a5c", label: "Disputed" },
            { color: "#ffb830", label: "Source" },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-2 text-xs text-dark-200">
              <div className="h-3 w-3 rounded-full" style={{ backgroundColor: item.color }} />
              {item.label}
            </div>
          ))}
        </div>
      </div>

      {/* Selected Node Detail */}
      {selectedNode && (
        <div className="glass-card">
          <div className="flex items-start justify-between">
            <div>
              <span className="risk-badge bg-dark-700 text-dark-200">{selectedNode.type}</span>
              <h3 className="mt-2 font-heading text-lg font-semibold text-white">
                {selectedNode.label}
              </h3>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-dark-400 hover:text-white"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
