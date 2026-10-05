# Technology Stack Research: Network Topology Graph Visualization

**Milestone:** v1.8 Interactive Network Topology Graph Diagram  
**Scope:** Graph engine, layout calculations, React 19 compatibility, and styling tokens.

---

## 1. Core Technology Options

| Approach | React 19 Compatibility | Bundle Impact | Strengths | Drawbacks | Recommendation |
|---|---|---|---|---|---|
| **Bespoke Interactive SVG + CSS Canvas** | **100% Native (Zero Dependencies)** | **~5 KB** | Seamless integration with existing CSS variables (`--bg-secondary`, `--card-border`, `--accent-blue`), zero npm install risks, perfect dark/light mode reactivity, hardware-accelerated SVG transforms, full control over bezier links and pulsing markers. | Requires manual pan/zoom math (~40 lines of matrix math). | **Highly Recommended (Primary)** |
| **`@xyflow/react` (React Flow v12+)** | Supports React 19 in v12.4+ | ~85 KB min+gzip | Rich ecosystem, built-in minimap and controls, drag-and-drop handles. | Heavy bundle size, CSS override complexity to match custom glassmorphic theme, peer dependency sensitivity in enterprise CI. | Secondary Alternative |
| **`reactflow` (v11 legacy)** | **Fails on React 19** | ~75 KB | Well known. | Strict React 18 peer dependency; install errors with `npm install` on React 19. | **Avoid** |
| **D3 Force / Visx** | Compatible | ~45 KB | Organic force-directed layout simulation. | Overkill for structured enterprise 3-tier hierarchical network topologies; non-deterministic layout causes nodes to bounce on re-renders. | **Avoid** |

---

## 2. Hierarchical Tier Layout Engine

Enterprise networks follow a deterministic 3-tier architecture:
- **Tier 1 (Core & WAN):** Routers, WAN transit gateways, DC backbones (Top row, `y ≈ 100px`).
- **Tier 2 (Distribution & Security):** Firewalls, distribution switches, policy enforcement (Middle row, `y ≈ 300px`).
- **Tier 3 (Campus & Access):** Catalyst access switches, wireless APs, edge clients (Bottom row, `y ≈ 500px`).

### Layout Algorithm:
1. Group nodes by `deriveDeviceTier(d.device_name)`.
2. Compute horizontal spacing per tier: `x = (index + 0.5) * (canvasWidth / tier.length)`.
3. Synthesize network links:
   - Core nodes link to Distribution nodes sharing geographical region or data center backbone.
   - Distribution switches link to Access nodes within their respective campus zones.
4. Curve link edges using cubic bezier curves (`M x1 y1 C x1 (y1+y2)/2, x2 (y1+y2)/2, x2 y2`) with directional flow animations.

---

## 3. Zoom, Pan & Viewport Math

- **Container:** Dedicated `<svg className="noc-topology-canvas">` with an inner `<g transform="translate(panX, panY) scale(zoomScale)">`.
- **Pan Interaction:** Pointer events (`onPointerDown`, `onPointerMove`, `onPointerUp`) with `setPointerCapture`.
- **Zoom Interaction:** Wheel event with delta clamping (`scale = Math.min(2.5, Math.max(0.4, scale * (1 - e.deltaY * 0.0015)))`).
- **Fit-to-Screen:** Automatically computes bounding box of all nodes and centers the graph on mount or via the "Reset Zoom" button.

---

## 4. Final Stack Decision

**Pure React 19 Native SVG Architecture:**
- Zero external package installation required.
- Directly leverages `lucide-react` icons (Server, Shield, Wifi, AlertTriangle).
- Uses native SVG `<circle>`, `<path>`, `<g>`, and `<foreignObject>` / HTML overlays.
- 100% theme-aware using CSS variables from `index.css` and `App.css`.
