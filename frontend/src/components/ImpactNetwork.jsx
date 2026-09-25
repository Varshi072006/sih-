import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { api } from "../services/api";
import { collaborationSocket } from "../services/collaborationSocket";

// ---------------------------------------------------------------------------
// Design Tokens & Configuration
// ---------------------------------------------------------------------------

const NODE_COLORS = {
  problem: { fill: "#ff6b35", stroke: "#ff9d6b", glow: "rgba(255,107,53,0.5)", label: "#fff", baseRadius: 10 },
  university: { fill: "#7c3aed", stroke: "#a78bfa", glow: "rgba(124,58,237,0.5)", label: "#fff", baseRadius: 13 },
  industry: { fill: "#059669", stroke: "#34d399", glow: "rgba(5,150,105,0.5)", label: "#fff", baseRadius: 13 },
  department: { fill: "#0284c7", stroke: "#38bdf8", glow: "rgba(2,132,199,0.5)", label: "#fff", baseRadius: 11 },
};

const LINK_STYLES = {
  assigned: { color: "#38bdf8", dash: "5 4", label: "Assigned" },
  suggestion: { color: "#a78bfa", dash: "4 3", label: "Suggestion" },
  investment: { color: "#f59e0b", dash: "none", label: "Investment" },
  technology: { color: "#34d399", dash: "none", label: "Tech Support" },
  implementation: { color: "#059669", dash: "none", label: "Implementation" },
  collaboration: { color: "#34d399", dash: "none", label: "Collaboration" },
  default: { color: "#475569", dash: "none", label: "Connected" },
};

// Initial fallback nodes to ensure instant live interaction before API loads
const DEMO_INITIAL_NODES = [
  { id: "P-C2I-001", label: "Drinking Water Shortage", type: "problem", district: "Ranchi", category: "water", status: "under_review", interactionCount: 4 },
  { id: "P-C2I-002", label: "Road Infrastructure Gap", type: "problem", district: "Dhanbad", category: "infrastructure", status: "university_opinion", interactionCount: 3 },
  { id: "P-C2I-003", label: "Smart Waste Management", type: "problem", district: "Jamshedpur", category: "sanitation", status: "implementation", interactionCount: 5 },
  { id: "P-C2I-004", label: "Rural Health Access", type: "problem", district: "Hazaribagh", category: "health", status: "verified", interactionCount: 2 },
  { id: "P-C2I-005", label: "Crop Disease Detection", type: "problem", district: "Giridih", category: "agriculture", status: "industry_participation", interactionCount: 3 },
  { id: "DEPT-1", label: "Drinking Water Dept", type: "department", district: "Ranchi", interactionCount: 3 },
  { id: "DEPT-2", label: "Road Construction Dept", type: "department", district: "Dhanbad", interactionCount: 2 },
  { id: "UNI-1", label: "BIT Mesra", type: "university", district: "Ranchi", interactionCount: 4 },
  { id: "UNI-2", label: "IIT (ISM) Dhanbad", type: "university", district: "Dhanbad", interactionCount: 5 },
  { id: "UNI-3", label: "NIT Jamshedpur", type: "university", district: "Jamshedpur", interactionCount: 3 },
  { id: "IND-1", label: "Tata Steel", type: "industry", district: "Jamshedpur", interactionCount: 4 },
  { id: "IND-2", label: "AgriTech Startup", type: "industry", district: "Ranchi", interactionCount: 3 },
  { id: "IND-3", label: "IoT Solutions Ltd", type: "industry", district: "Bokaro", interactionCount: 3 },
];

const DEMO_INITIAL_LINKS = [
  { source: "P-C2I-001", target: "DEPT-1", type: "assigned", relationship: "Assigned Department", interactionCount: 1 },
  { source: "P-C2I-001", target: "UNI-1", type: "suggestion", relationship: "Suggestion", interactionCount: 2 },
  { source: "P-C2I-001", target: "IND-3", type: "collaboration", relationship: "Technology Support", interactionCount: 1 },
  { source: "P-C2I-002", target: "DEPT-2", type: "assigned", relationship: "Assigned Department", interactionCount: 1 },
  { source: "P-C2I-002", target: "UNI-2", type: "suggestion", relationship: "Suggestion", interactionCount: 1 },
  { source: "P-C2I-002", target: "IND-1", type: "investment", relationship: "CSR Investment", interactionCount: 1 },
  { source: "P-C2I-003", target: "UNI-1", type: "suggestion", relationship: "Technical Guidance", interactionCount: 2 },
  { source: "P-C2I-003", target: "IND-1", type: "implementation", relationship: "Implementation", interactionCount: 1 },
  { source: "P-C2I-004", target: "UNI-3", type: "suggestion", relationship: "Suggestion", interactionCount: 1 },
  { source: "P-C2I-005", target: "UNI-2", type: "suggestion", relationship: "Suggestion", interactionCount: 2 },
  { source: "P-C2I-005", target: "IND-2", type: "collaboration", relationship: "Pilot Deployment", interactionCount: 1 },
];

function formatTimeAgo(timestamp) {
  if (!timestamp) return "just now";
  const seconds = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000);
  if (seconds < 10) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

// ---------------------------------------------------------------------------
// Animated Particle along Link (The beloved previous connection animation)
// ---------------------------------------------------------------------------

function LinkParticle({ x1, y1, x2, y2, color, delay = 0, isHighlighted = false }) {
  const [t, setT] = useState(delay);
  const rafRef = useRef(null);

  useEffect(() => {
    let start = null;
    const dur = isHighlighted ? 1500 : 2200;
    function animate(ts) {
      if (!start) start = ts;
      const elapsed = (ts - start) / dur + delay;
      setT(elapsed % 1);
      rafRef.current = requestAnimationFrame(animate);
    }
    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [delay, isHighlighted]);

  const px = x1 + (x2 - x1) * t;
  const py = y1 + (y2 - y1) * t;

  return (
    <g className="pointer-events-none">
      {/* Outer soft glow particle */}
      <circle cx={px} cy={py} r={isHighlighted ? 4.5 : 3.2} fill={color} opacity={0.85}>
        <animate attributeName="opacity" values="0.3;1;0.3" dur="2s" repeatCount="indefinite" begin={`${delay}s`} />
      </circle>
      {/* Bright core center */}
      <circle cx={px} cy={py} r={isHighlighted ? 2.4 : 1.6} fill="#ffffff" opacity={0.95} />
    </g>
  );
}

// ---------------------------------------------------------------------------
// Force Simulation Engine with Stability & Dragging Support
// ---------------------------------------------------------------------------

function useForceSimulation(nodes, links, width, height, draggedNode) {
  const posRef = useRef({});
  const velRef = useRef({});
  const [positions, setPositions] = useState({});

  useEffect(() => {
    if (!nodes.length) return;

    const p = posRef.current;
    const v = velRef.current;

    // Preserve existing node positions, only initialize new nodes
    nodes.forEach((n, i) => {
      if (!p[n.id]) {
        const angle = (i / nodes.length) * 2 * Math.PI;
        const r = Math.min(width, height) * 0.28;
        p[n.id] = {
          x: width / 2 + r * Math.cos(angle) + (Math.random() - 0.5) * 35,
          y: height / 2 + r * Math.sin(angle) + (Math.random() - 0.5) * 35,
        };
        v[n.id] = { x: 0, y: 0 };
      }
    });

    let frame;
    let tick = 0;
    const MAX_TICKS = 320;

    function simulate() {
      tick++;
      const alpha = Math.max(0.002, 1 - tick / MAX_TICKS);
      const activeIds = nodes.map((n) => n.id).filter((id) => p[id]);

      // Repulsion between all nodes
      for (let i = 0; i < activeIds.length; i++) {
        for (let j = i + 1; j < activeIds.length; j++) {
          const a = p[activeIds[i]];
          const b = p[activeIds[j]];
          if (!a || !b) continue;
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          if (dist > 320) continue;
          const force = (3200 / (dist * dist)) * alpha;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          v[activeIds[i]].x -= fx;
          v[activeIds[i]].y -= fy;
          v[activeIds[j]].x += fx;
          v[activeIds[j]].y += fy;
        }
      }

      // Attraction along links
      links.forEach((l) => {
        const srcId = typeof l.source === "object" ? l.source.id : l.source;
        const tgtId = typeof l.target === "object" ? l.target.id : l.target;
        const src = p[srcId];
        const tgt = p[tgtId];
        if (!src || !tgt) return;
        const dx = tgt.x - src.x;
        const dy = tgt.y - src.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const ideal = 125;
        const force = ((dist - ideal) / dist) * 0.08 * alpha;
        const fx = dx * force;
        const fy = dy * force;
        v[srcId].x += fx;
        v[srcId].y += fy;
        v[tgtId].x -= fx;
        v[tgtId].y -= fy;
      });

      // Center gravity
      activeIds.forEach((id) => {
        v[id].x += (width / 2 - p[id].x) * 0.0055 * alpha;
        v[id].y += (height / 2 - p[id].y) * 0.0055 * alpha;
      });

      // Apply velocity with damping
      activeIds.forEach((id) => {
        if (draggedNode && draggedNode.id === id) {
          p[id].x = draggedNode.x;
          p[id].y = draggedNode.y;
          v[id].x = 0;
          v[id].y = 0;
          return;
        }
        v[id].x *= 0.86;
        v[id].y *= 0.86;
        p[id].x += v[id].x;
        p[id].y += v[id].y;
        // Clamp to canvas padding
        p[id].x = Math.max(30, Math.min(width - 30, p[id].x));
        p[id].y = Math.max(30, Math.min(height - 30, p[id].y));
      });

      setPositions({ ...p });

      if (tick < MAX_TICKS) {
        frame = requestAnimationFrame(simulate);
      }
    }

    frame = requestAnimationFrame(simulate);
    return () => cancelAnimationFrame(frame);
  }, [nodes, links, width, height, draggedNode]);

  return positions;
}

// ---------------------------------------------------------------------------
// Tooltip
// ---------------------------------------------------------------------------

function NodeTooltip({ node, x, y }) {
  if (!node) return null;
  const cfg = NODE_COLORS[node.type] || NODE_COLORS.problem;
  return (
    <div
      className="pointer-events-none absolute z-50 max-w-[220px] rounded-2xl border border-white/20 bg-forest-950/95 p-3 text-xs text-white shadow-2xl backdrop-blur-md"
      style={{ left: Math.min(x + 14, window.innerWidth - 240), top: y - 10, transform: "translateY(-50%)" }}
    >
      <div className="mb-1 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full" style={{ background: cfg.fill }} />
          <span className="font-semibold uppercase tracking-wider text-[10px] opacity-75">{node.type}</span>
        </div>
        {node.interactionCount != null && (
          <span className="text-[10px] text-emerald-400 font-semibold">{node.interactionCount} interactions</span>
        )}
      </div>
      <p className="font-semibold leading-5 text-sm">{node.label}</p>
      {node.district && <p className="mt-1 opacity-60 text-[11px]">{node.district}</p>}
      {node.category && <p className="opacity-60 text-[11px] capitalize">{node.category}</p>}
      {node.status && (
        <p className="mt-1.5 rounded-full bg-white/10 px-2 py-0.5 text-center text-[10px] capitalize text-amber-200">
          {node.status.replace(/_/g, " ")}
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function ImpactNetwork({ compact = false, problemId = null }) {
  const containerRef = useRef(null);
  const svgRef = useRef(null);

  const [size, setSize] = useState({ width: 800, height: compact ? 420 : 580 });
  const [graphData, setGraphData] = useState({ nodes: DEMO_INITIAL_NODES, links: DEMO_INITIAL_LINKS });
  const [filter, setFilter] = useState("all");
  const [loaded, setLoaded] = useState(false);
  const [onlineCount, setOnlineCount] = useState(3);

  // Interaction State
  const [hoveredNode, setHoveredNode] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [activityOpen, setActivityOpen] = useState(!compact);
  const [recentEvents, setRecentEvents] = useState([]);

  // Pan & Zoom
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const isPanningRef = useRef(false);
  const startPanRef = useRef({ x: 0, y: 0 });

  // Dragging node
  const [draggedNode, setDraggedNode] = useState(null);

  // Active pulses & presence
  const [activePulses, setActivePulses] = useState({}); // nodeId -> timestamp
  const [presenceNodes, setPresenceNodes] = useState(new Set()); // nodeIds with active viewers

  // Responsive observer
  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver((entries) => {
      const { width } = entries[0].contentRect;
      setSize({
        width: Math.max(300, width),
        height: compact ? 420 : Math.max(480, Math.min(640, width * 0.65)),
      });
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, [compact]);

  // Load Initial Network Data from API
  useEffect(() => {
    api("/api/network")
      .then((data) => {
        if (data.nodes && data.nodes.length > 2) {
          // Merge deduplicated nodes
          const nodeMap = new Map();
          data.nodes.forEach((n) => nodeMap.set(n.id, n));

          const cleanLinks = (data.links || []).map((l) => ({
            ...l,
            interactionCount: l.interactionCount || 1,
          }));

          setGraphData({
            nodes: Array.from(nodeMap.values()),
            links: cleanLinks,
          });

          if (data.recentEvents?.length) {
            setRecentEvents(data.recentEvents);
          }
        }
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, []);

  // Real-Time Socket Connection
  useEffect(() => {
    collaborationSocket.connect("global", "Collaborator");

    const unsubPresence = collaborationSocket.subscribePresence((count) => {
      setOnlineCount(count);
    });

    const unsubEvents = collaborationSocket.subscribe((event) => {
      if (event.type === "NODE_PRESENCE") {
        setPresenceNodes((prev) => {
          const next = new Set(prev);
          if (event.active) next.add(event.nodeId);
          else next.delete(event.nodeId);
          return next;
        });
        return;
      }

      handleCollaborationEvent(event);
    });

    return () => {
      unsubPresence();
      unsubEvents();
      collaborationSocket.disconnect();
    };
  }, []);

  // Handle incoming collaboration event
  const handleCollaborationEvent = useCallback((event) => {
    const now = Date.now();

    // 1. Prepend to live activity feed
    setRecentEvents((prev) => {
      const exists = prev.some((e) => e.eventId === event.eventId);
      if (exists) return prev;
      return [event, ...prev.slice(0, 19)];
    });

    // 2. Update graph data
    setGraphData((prev) => {
      const nodeMap = new Map();
      prev.nodes.forEach((n) => nodeMap.set(n.id, { ...n }));

      const targetProblemId = event.problemId ? (event.problemId.startsWith("P-") ? event.problemId : `P-${event.problemId}`) : null;
      let affectedNodeId = null;

      if (targetProblemId && nodeMap.has(targetProblemId)) {
        const prob = nodeMap.get(targetProblemId);
        prob.interactionCount = (prob.interactionCount || 0) + 1;
        if (event.newStatus) prob.status = event.newStatus;
        affectedNodeId = targetProblemId;
      }

      let actorNodeId = null;
      if (event.actorId) {
        actorNodeId = event.actorId;
      } else if (event.universityId || event.universityName) {
        actorNodeId = event.universityId || `UNI-${event.universityName.replace(/\s+/g, "_")}`;
      } else if (event.industryId || event.industryName) {
        actorNodeId = event.industryId || `IND-${event.industryName.replace(/\s+/g, "_")}`;
      } else if (event.departmentId || event.departmentName) {
        actorNodeId = event.departmentId || `DEPT-${event.departmentName.replace(/\s+/g, "_")}`;
      }

      if (actorNodeId) {
        if (!nodeMap.has(actorNodeId)) {
          const type = event.actorType || (actorNodeId.startsWith("UNI-") ? "university" : actorNodeId.startsWith("IND-") ? "industry" : "department");
          const label = event.actorName || event.universityName || event.industryName || event.departmentName || "Partner";
          nodeMap.set(actorNodeId, {
            id: actorNodeId,
            label,
            type,
            interactionCount: 1,
          });
        } else {
          const actor = nodeMap.get(actorNodeId);
          actor.interactionCount = (actor.interactionCount || 0) + 1;
        }
        affectedNodeId = actorNodeId;
      }

      // Deduplicate links
      const links = prev.links.map((l) => ({ ...l }));
      if (targetProblemId && actorNodeId) {
        const relType = (event.relationship || (actorNodeId.startsWith("UNI-") ? "suggestion" : actorNodeId.startsWith("DEPT-") ? "assigned" : "collaboration")).toLowerCase();

        const existingLink = links.find((l) => {
          const srcId = typeof l.source === "object" ? l.source.id : l.source;
          const tgtId = typeof l.target === "object" ? l.target.id : l.target;
          return (srcId === targetProblemId && tgtId === actorNodeId) || (srcId === actorNodeId && tgtId === targetProblemId);
        });

        if (existingLink) {
          existingLink.interactionCount = (existingLink.interactionCount || 1) + 1;
          existingLink.type = relType;
        } else {
          links.push({
            source: targetProblemId,
            target: actorNodeId,
            type: relType,
            relationship: event.relationship || "Collaboration",
            interactionCount: 1,
          });
        }
      }

      // Trigger pulse animation on affected node
      if (affectedNodeId) {
        setActivePulses((prevP) => ({ ...prevP, [affectedNodeId]: now }));
        setTimeout(() => {
          setActivePulses((prevP) => {
            const nextP = { ...prevP };
            delete nextP[affectedNodeId];
            return nextP;
          });
        }, 3000);
      }

      return {
        nodes: Array.from(nodeMap.values()),
        links,
      };
    });
  }, []);

  // Filtered graph items
  const filteredNodes = useMemo(() => {
    let list = graphData.nodes;
    if (problemId) {
      const targetId = problemId.startsWith("P-") ? problemId : `P-${problemId}`;
      const connected = new Set([targetId, problemId]);
      graphData.links.forEach((l) => {
        const s = typeof l.source === "object" ? l.source.id : l.source;
        const t = typeof l.target === "object" ? l.target.id : l.target;
        if (s === targetId || s === problemId) connected.add(t);
        if (t === targetId || t === problemId) connected.add(s);
      });
      list = list.filter((n) => connected.has(n.id));
    } else if (filter !== "all") {
      list = list.filter((n) => n.type === filter);
    }
    return list;
  }, [graphData.nodes, graphData.links, filter, problemId]);

  const filteredNodeIds = useMemo(() => new Set(filteredNodes.map((n) => n.id)), [filteredNodes]);

  const filteredLinks = useMemo(
    () =>
      graphData.links.filter((l) => {
        const s = typeof l.source === "object" ? l.source.id : l.source;
        const t = typeof l.target === "object" ? l.target.id : l.target;
        return filteredNodeIds.has(s) && filteredNodeIds.has(t);
      }),
    [graphData.links, filteredNodeIds]
  );

  // Compute Positions using Force Simulation
  const positions = useForceSimulation(filteredNodes, filteredLinks, size.width, size.height, draggedNode);

  // Mouse Move over Node
  const handleNodeMouseMove = useCallback((e, node) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    setHoveredNode(node);
  }, []);

  // Node Click
  const handleNodeClick = useCallback((node) => {
    setSelectedNode((prev) => (prev?.id === node.id ? null : node));
    collaborationSocket.emitNodePresence(node.id, true);
    setTimeout(() => {
      collaborationSocket.emitNodePresence(node.id, false);
    }, 12000);
  }, []);

  // Node Drag Handlers
  const handleNodeMouseDown = (e, node) => {
    e.stopPropagation();
    const pos = positions[node.id];
    if (!pos) return;
    setDraggedNode({ id: node.id, x: pos.x, y: pos.y, startX: e.clientX, startY: e.clientY });
  };

  const handleContainerMouseMove = (e) => {
    if (draggedNode) {
      const dx = (e.clientX - draggedNode.startX) / zoom;
      const dy = (e.clientY - draggedNode.startY) / zoom;
      setDraggedNode((prev) => ({
        ...prev,
        x: prev.x + dx,
        y: prev.y + dy,
        startX: e.clientX,
        startY: e.clientY,
      }));
    } else if (isPanningRef.current) {
      const dx = e.clientX - startPanRef.current.x;
      const dy = e.clientY - startPanRef.current.y;
      setPan((prev) => ({ x: prev.x + dx, y: prev.y + dy }));
      startPanRef.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleContainerMouseUp = () => {
    setDraggedNode(null);
    isPanningRef.current = false;
  };

  const handleContainerMouseDown = (e) => {
    if (e.target.tagName === "svg" || e.target.tagName === "rect") {
      isPanningRef.current = true;
      startPanRef.current = { x: e.clientX, y: e.clientY };
      setSelectedNode(null);
    }
  };

  // Search
  const handleSearchChange = (e) => {
    const q = e.target.value;
    setSearchQuery(q);
    if (!q.trim()) {
      setSearchResults([]);
      return;
    }
    const lower = q.toLowerCase();
    const matches = graphData.nodes
      .filter((n) => n.label.toLowerCase().includes(lower) || (n.district && n.district.toLowerCase().includes(lower)))
      .slice(0, 5);
    setSearchResults(matches);
  };

  const handleSelectSearchResult = (node) => {
    setSelectedNode(node);
    setSearchQuery("");
    setSearchResults([]);
    const pos = positions[node.id];
    if (pos) {
      setPan({ x: size.width / 2 - pos.x * 1.5, y: size.height / 2 - pos.y * 1.5 });
      setZoom(1.5);
    }
    setActivePulses((prev) => ({ ...prev, [node.id]: Date.now() }));
  };

  // Zoom controls
  const handleZoomIn = () => setZoom((z) => Math.min(2.5, z * 1.25));
  const handleZoomOut = () => setZoom((z) => Math.max(0.6, z * 0.8));
  const handleResetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setSelectedNode(null);
  };

  // Highlight network
  const activeFocusNode = hoveredNode || selectedNode;

  // Counts for Stats Bar
  const counts = useMemo(
    () => ({
      problems: graphData.nodes.filter((n) => n.type === "problem").length,
      universities: graphData.nodes.filter((n) => n.type === "university").length,
      industries: graphData.nodes.filter((n) => n.type === "industry").length,
      departments: graphData.nodes.filter((n) => n.type === "department").length,
      links: graphData.links.length,
    }),
    [graphData]
  );

  return (
    <div
      ref={containerRef}
      onMouseMove={handleContainerMouseMove}
      onMouseUp={handleContainerMouseUp}
      onMouseDown={handleContainerMouseDown}
      className="relative rounded-[28px] border border-[#203348] bg-[#07111f] overflow-hidden shadow-[0_20px_60px_rgba(7,17,31,0.45)] text-slate-200 select-none font-sans"
    >
      {/* ------------------------------------------------------------------- */}
      {/* 1. Header with Live Participant Indicator & Search                   */}
      {/* ------------------------------------------------------------------- */}
      <div className="flex flex-col gap-4 border-b border-white/10 px-6 py-4 lg:flex-row lg:items-center lg:justify-between bg-forest-950/40 backdrop-blur-md">
        <div>
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-400">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span>{onlineCount} collaborators online</span>
            </span>
            <span className="text-xs text-slate-400 hidden sm:inline">· Live Connection Network</span>
          </div>
          <h3 className="mt-1 font-serif text-xl text-white">Live Collaboration Graph</h3>
        </div>

        {/* Live Search & Filter Bar */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Minimal Search Input */}
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={handleSearchChange}
              placeholder="Search problems, universities, departments..."
              className="w-56 md:w-64 rounded-full border border-white/15 bg-white/5 px-3.5 py-1.5 text-xs text-white placeholder-white/40 focus:border-emerald-400 focus:outline-none focus:ring-1 focus:ring-emerald-400 transition"
            />
            {searchResults.length > 0 && (
              <div className="absolute left-0 top-full mt-1.5 w-64 rounded-2xl border border-white/15 bg-[#0a1829] p-1.5 shadow-2xl z-50">
                {searchResults.map((n) => (
                  <button
                    key={n.id}
                    type="button"
                    onClick={() => handleSelectSearchResult(n)}
                    className="w-full text-left rounded-xl px-3 py-2 text-xs hover:bg-white/10 flex items-center justify-between transition"
                  >
                    <span className="truncate text-white font-medium">{n.label}</span>
                    <span
                      className="ml-2 text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded-md"
                      style={{
                        background: `${NODE_COLORS[n.type]?.fill}20`,
                        color: NODE_COLORS[n.type]?.fill,
                      }}
                    >
                      {n.type}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1.5">
            {["all", "problem", "university", "industry", "department"].map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFilter(f)}
                className={`rounded-full px-3 py-1 text-[11px] font-semibold transition ${
                  filter === f
                    ? "bg-emerald-500 text-forest-950 font-bold"
                    : "border border-white/10 bg-white/5 text-white/60 hover:bg-white/10 hover:text-white"
                }`}
              >
                {f === "all" ? "All" : f.charAt(0).toUpperCase() + f.slice(1) + "s"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* 2. Stats Bar                                                        */}
      {/* ------------------------------------------------------------------- */}
      <div className="grid grid-cols-5 divide-x divide-white/10 border-b border-white/10 bg-black/20 text-center">
        {[
          { label: "Problems", value: counts.problems, color: "#ff6b35" },
          { label: "Universities", value: counts.universities, color: "#7c3aed" },
          { label: "Industries", value: counts.industries, color: "#059669" },
          { label: "Departments", value: counts.departments, color: "#0284c7" },
          { label: "Connections", value: counts.links, color: "#f59e0b" },
        ].map(({ label, value, color }) => (
          <div key={label} className="py-2.5 px-1 flex flex-col items-center">
            <span className="font-serif text-xl font-bold" style={{ color }}>{value}</span>
            <span className="text-[10px] uppercase tracking-wider text-white/45">{label}</span>
          </div>
        ))}
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* 3. SVG Graph Canvas Area with Beloved Connection Animation          */}
      {/* ------------------------------------------------------------------- */}
      <div className="relative" style={{ height: size.height }}>
        {!loaded && (
          <div className="absolute inset-0 z-30 flex items-center justify-center bg-[#07111f]/80 backdrop-blur-sm">
            <div className="flex gap-2">
              {[0, 1, 2].map((i) => (
                <div key={i} className="h-2.5 w-2.5 animate-bounce rounded-full bg-emerald-400" style={{ animationDelay: `${i * 0.15}s` }} />
              ))}
            </div>
          </div>
        )}

        <svg ref={svgRef} width={size.width} height={size.height} className="absolute inset-0 cursor-grab active:cursor-grabbing">
          <defs>
            {Object.entries(NODE_COLORS).map(([type, c]) => (
              <radialGradient key={type} id={`glow-${type}`} cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor={c.fill} stopOpacity="0.65" />
                <stop offset="100%" stopColor={c.fill} stopOpacity="0" />
              </radialGradient>
            ))}
            <filter id="blur-glow">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Background rect to capture pan events */}
          <rect width={size.width} height={size.height} fill="transparent" />

          {/* Pan & Zoom Transformed Container */}
          <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
            {/* ------------------------------------------------------------- */}
            {/* Connection Lines & Animated Moving Particles                  */}
            {/* ------------------------------------------------------------- */}
            {filteredLinks.map((link, i) => {
              const srcId = typeof link.source === "object" ? link.source.id : link.source;
              const tgtId = typeof link.target === "object" ? link.target.id : link.target;
              const src = positions[srcId];
              const tgt = positions[tgtId];
              if (!src || !tgt) return null;

              const style = LINK_STYLES[link.type] || LINK_STYLES.default;
              const isConnectedLink = activeFocusNode && (activeFocusNode.id === srcId || activeFocusNode.id === tgtId);
              const isDimmed = activeFocusNode && !isConnectedLink;

              return (
                <g key={`link-${srcId}-${tgtId}-${i}`} style={{ opacity: isDimmed ? 0.2 : 1, transition: "opacity 0.2s" }}>
                  {/* Connection Line */}
                  <line
                    x1={src.x}
                    y1={src.y}
                    x2={tgt.x}
                    y2={tgt.y}
                    stroke={style.color}
                    strokeWidth={isConnectedLink ? 2.2 : 1.2}
                    strokeOpacity={isConnectedLink ? 0.95 : 0.35}
                    strokeDasharray={style.dash}
                  />

                  {/* Animated Particle Moving along Connection (Beloved Previous Animation) */}
                  <LinkParticle
                    x1={src.x}
                    y1={src.y}
                    x2={tgt.x}
                    y2={tgt.y}
                    color={style.color}
                    delay={(i * 0.37) % 1}
                    isHighlighted={isConnectedLink}
                  />
                </g>
              );
            })}

            {/* ------------------------------------------------------------- */}
            {/* Graph Nodes                                                   */}
            {/* ------------------------------------------------------------- */}
            {filteredNodes.map((node) => {
              const pos = positions[node.id];
              if (!pos) return null;

              const c = NODE_COLORS[node.type] || NODE_COLORS.problem;
              const activityBonus = Math.min(4, (node.interactionCount || 0) * 0.4);
              const r = c.baseRadius + activityBonus;

              const isHov = hoveredNode?.id === node.id;
              const isSel = selectedNode?.id === node.id;
              const isTarget = isHov || isSel;

              const isConnected =
                activeFocusNode &&
                filteredLinks.some((l) => {
                  const s = typeof l.source === "object" ? l.source.id : l.source;
                  const t = typeof l.target === "object" ? l.target.id : l.target;
                  return (s === activeFocusNode.id && t === node.id) || (t === activeFocusNode.id && s === node.id);
                });

              const isDimmed = activeFocusNode && !isTarget && !isConnected;
              const isPulsing = activePulses[node.id];
              const hasPresence = presenceNodes.has(node.id);

              return (
                <g
                  key={node.id}
                  transform={`translate(${pos.x},${pos.y})`}
                  style={{
                    cursor: "pointer",
                    opacity: isDimmed ? 0.3 : 1,
                    transition: "opacity 0.2s ease",
                  }}
                  onMouseMove={(e) => handleNodeMouseMove(e, node)}
                  onMouseLeave={() => setHoveredNode(null)}
                  onClick={() => handleNodeClick(node)}
                  onMouseDown={(e) => handleNodeMouseDown(e, node)}
                >
                  {/* Outer Glow Halo */}
                  {(isTarget || isConnected || isPulsing) && (
                    <circle r={r + 12} fill={`url(#glow-${node.type})`} opacity={0.85} />
                  )}

                  {/* Node Activity Pulse Ring (Previous style animated pulse) */}
                  {(isTarget || isPulsing) && (
                    <circle r={r + 6} fill="none" stroke={c.stroke} strokeWidth={isPulsing ? 2.2 : 1.5} opacity={0.7}>
                      <animate attributeName="r" values={`${r + 4};${r + 18};${r + 4}`} dur={isPulsing ? "1.2s" : "1.8s"} repeatCount="indefinite" />
                      <animate attributeName="opacity" values="0.75;0;0.75" dur={isPulsing ? "1.2s" : "1.8s"} repeatCount="indefinite" />
                    </circle>
                  )}

                  {/* Main Node Circle */}
                  <circle
                    r={isTarget ? r + 3 : r}
                    fill={c.fill}
                    stroke={c.stroke}
                    strokeWidth={isTarget ? 2.6 : 1.6}
                    filter={isTarget ? "url(#blur-glow)" : undefined}
                    style={{ transition: "r 0.2s ease" }}
                  />

                  {/* Inner shine gloss highlight */}
                  <circle r={r * 0.45} cx={-r * 0.22} cy={-r * 0.22} fill="white" opacity={0.28} />

                  {/* Presence on Node Indicator (Active Collaborator Viewing) */}
                  {hasPresence && (
                    <circle cx={r * 0.75} cy={-r * 0.75} r={3.6} fill="#10b981" stroke="#ffffff" strokeWidth={1} />
                  )}

                  {/* Node Label */}
                  <text
                    y={r + 14}
                    textAnchor="middle"
                    fill="white"
                    fontSize={isTarget ? 11 : 9.5}
                    fontWeight={isTarget ? "700" : "500"}
                    opacity={isTarget || isConnected || !activeFocusNode ? 1 : 0.3}
                    style={{ pointerEvents: "none", transition: "opacity 0.2s" }}
                  >
                    {node.label.length > 19 && !isTarget ? `${node.label.slice(0, 18)}…` : node.label}
                  </text>
                </g>
              );
            })}
          </g>
        </svg>

        {/* ----------------------------------------------------------------- */}
        {/* Tooltip on Hover                                                  */}
        {/* ----------------------------------------------------------------- */}
        {hoveredNode && !selectedNode && <NodeTooltip node={hoveredNode} x={tooltipPos.x} y={tooltipPos.y} />}

        {/* ----------------------------------------------------------------- */}
        {/* Graph Controls (Zoom In, Zoom Out, Reset View)                    */}
        {/* ----------------------------------------------------------------- */}
        <div className="absolute top-4 left-4 z-20 flex flex-col gap-1.5 rounded-2xl border border-white/10 bg-[#07111f]/85 p-1.5 shadow-xl backdrop-blur-md">
          <button
            type="button"
            onClick={handleZoomIn}
            title="Zoom In"
            className="h-8 w-8 rounded-xl flex items-center justify-center text-sm font-bold text-white/80 hover:bg-white/10 hover:text-white transition"
          >
            +
          </button>
          <button
            type="button"
            onClick={handleZoomOut}
            title="Zoom Out"
            className="h-8 w-8 rounded-xl flex items-center justify-center text-sm font-bold text-white/80 hover:bg-white/10 hover:text-white transition"
          >
            −
          </button>
          <div className="h-px bg-white/10 my-0.5" />
          <button
            type="button"
            onClick={handleResetView}
            title="Reset View"
            className="h-8 w-8 rounded-xl flex items-center justify-center text-xs text-white/80 hover:bg-white/10 hover:text-white transition"
          >
            ⛶
          </button>
        </div>

        {/* ----------------------------------------------------------------- */}
        {/* 4. Live Activity Floating Panel (Req 4)                            */}
        {/* ----------------------------------------------------------------- */}
        <div className="absolute top-4 right-4 z-20 max-w-xs w-72">
          {activityOpen ? (
            <div className="rounded-2xl border border-white/15 bg-[#07111f]/90 p-3 shadow-2xl backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2">
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400">Live Activity</span>
                </div>
                <button
                  type="button"
                  onClick={() => setActivityOpen(false)}
                  className="text-xs text-white/50 hover:text-white transition px-1"
                  title="Minimize"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-2 max-h-44 overflow-y-auto pr-1">
                {recentEvents.length === 0 ? (
                  <p className="text-xs text-white/40 italic py-2 text-center">Listening for live updates...</p>
                ) : (
                  recentEvents.map((evt) => (
                    <div
                      key={evt.eventId}
                      onClick={() => {
                        const targetId = evt.problemId ? (evt.problemId.startsWith("P-") ? evt.problemId : `P-${evt.problemId}`) : evt.actorId;
                        const node = graphData.nodes.find((n) => n.id === targetId || n.id === evt.actorId);
                        if (node) handleNodeClick(node);
                      }}
                      className="group cursor-pointer rounded-xl border border-white/5 bg-white/5 p-2 hover:bg-white/10 transition text-[11px]"
                    >
                      <div className="flex items-start justify-between gap-1 text-slate-300">
                        <span className="font-semibold text-white group-hover:text-emerald-300 transition">
                          {evt.actorName || evt.universityName || evt.departmentName || evt.industryName || "Collaborator"}
                        </span>
                        <span className="text-[10px] text-white/40 whitespace-nowrap">{formatTimeAgo(evt.timestamp)}</span>
                      </div>
                      <p className="text-white/70 mt-0.5 leading-snug line-clamp-2">
                        {evt.summary || (evt.problemTitle ? `action on ${evt.problemTitle}` : "collaboration action")}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setActivityOpen(true)}
              className="flex items-center gap-2 rounded-full border border-white/15 bg-[#07111f]/90 px-3 py-1.5 text-xs text-white shadow-xl backdrop-blur-md hover:bg-white/10 transition"
            >
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Live Activity ({recentEvents.length})</span>
            </button>
          )}
        </div>

        {/* ----------------------------------------------------------------- */}
        {/* 5. Selected Node Details Drawer / Bottom Sheet                     */}
        {/* ----------------------------------------------------------------- */}
        {selectedNode && (
          <div className="absolute bottom-4 right-4 z-30 max-w-sm w-80 rounded-2xl border border-white/20 bg-forest-950/95 p-4 shadow-2xl backdrop-blur-lg animate-in fade-in duration-200">
            <div className="flex items-start justify-between border-b border-white/10 pb-3">
              <div>
                <span
                  className="rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider"
                  style={{
                    background: `${NODE_COLORS[selectedNode.type]?.fill}25`,
                    color: NODE_COLORS[selectedNode.type]?.fill,
                  }}
                >
                  {selectedNode.type}
                </span>
                <h4 className="mt-1 font-serif text-lg font-bold text-white leading-tight">{selectedNode.label}</h4>
                {selectedNode.district && <p className="text-xs text-white/50">{selectedNode.district}</p>}
              </div>
              <button
                type="button"
                onClick={() => setSelectedNode(null)}
                className="text-white/40 hover:text-white p-1 text-sm transition"
              >
                ✕
              </button>
            </div>

            <div className="mt-3 space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-white/5">
                <span className="text-white/50">Total Interactions:</span>
                <span className="font-semibold text-emerald-400">{selectedNode.interactionCount || 1}</span>
              </div>
              {selectedNode.status && (
                <div className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-white/50">Status:</span>
                  <span className="capitalize text-amber-300 font-medium">{selectedNode.status.replace(/_/g, " ")}</span>
                </div>
              )}
              {selectedNode.category && (
                <div className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-white/50">Category:</span>
                  <span className="capitalize text-white/80">{selectedNode.category}</span>
                </div>
              )}

              {/* Connected Collaborators summary */}
              <div className="pt-2">
                <p className="text-[10px] uppercase font-bold tracking-wider text-white/40 mb-1.5">Direct Connections</p>
                <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
                  {graphData.links
                    .filter((l) => {
                      const s = typeof l.source === "object" ? l.source.id : l.source;
                      const t = typeof l.target === "object" ? l.target.id : l.target;
                      return s === selectedNode.id || t === selectedNode.id;
                    })
                    .map((l, i) => {
                      const otherId = (typeof l.source === "object" ? l.source.id : l.source) === selectedNode.id
                        ? (typeof l.target === "object" ? l.target.id : l.target)
                        : (typeof l.source === "object" ? l.source.id : l.source);
                      const otherNode = graphData.nodes.find((n) => n.id === otherId);
                      return (
                        <button
                          key={i}
                          type="button"
                          onClick={() => otherNode && handleNodeClick(otherNode)}
                          className="rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-[11px] text-white/80 hover:bg-white/15 hover:text-white transition"
                        >
                          {otherNode?.label || otherId} · <span className="opacity-60">{l.relationship || l.type}</span>
                        </button>
                      );
                    })}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ----------------------------------------------------------------- */}
        {/* 6. Minimal Legend                                                 */}
        {/* ----------------------------------------------------------------- */}
        <div className="absolute bottom-3 left-4 z-10 flex flex-wrap gap-2 text-xs">
          {[
            { type: "problem", label: "Problem", color: "#ff6b35" },
            { type: "university", label: "University", color: "#7c3aed" },
            { type: "industry", label: "Industry", color: "#059669" },
            { type: "department", label: "Department", color: "#0284c7" },
          ].map(({ label, color }) => (
            <div key={label} className="flex items-center gap-1.5 rounded-full border border-white/10 bg-black/40 px-2.5 py-1 backdrop-blur-sm">
              <span className="h-2 w-2 rounded-full" style={{ background: color }} />
              <span className="text-[10px] font-medium text-white/80">{label}</span>
            </div>
          ))}
          <div className="flex items-center gap-1.5 rounded-full border border-white/10 bg-black/40 px-2.5 py-1 backdrop-blur-sm">
            <svg width="14" height="4"><line x1="0" y1="2" x2="14" y2="2" stroke="#a78bfa" strokeWidth="1.5" strokeDasharray="3 2" /></svg>
            <span className="text-[10px] font-medium text-white/80">Suggestion</span>
          </div>
          <div className="flex items-center gap-1.5 rounded-full border border-white/10 bg-black/40 px-2.5 py-1 backdrop-blur-sm">
            <svg width="14" height="4"><line x1="0" y1="2" x2="14" y2="2" stroke="#34d399" strokeWidth="1.5" /></svg>
            <span className="text-[10px] font-medium text-white/80">Collaboration</span>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* 7. Footer Information Bar                                           */}
      {/* ------------------------------------------------------------------- */}
      <div className="border-t border-white/10 px-6 py-2.5 text-[11px] text-white/50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 bg-black/20">
        <div>Drag nodes to adjust layout · Hover any node to explore connections · Moving particles represent live collaboration</div>
        <div className="flex items-center gap-2">
          <span className="text-emerald-400">● Live Connection Active</span>
        </div>
      </div>
    </div>
  );
}
