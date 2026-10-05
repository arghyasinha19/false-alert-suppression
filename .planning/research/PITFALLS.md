# Pitfalls Research: Interactive Network Topology Graph

**Milestone:** v1.8 Interactive Network Topology Graph Diagram  
**Scope:** Performance, event handling, responsive canvas sizing, and React lifecycle.

---

## 1. Canvas Event Capture & Scrolling Contention
- **Pitfall:** Mouse wheel zoom over the graph canvas accidentally scrolls the entire dashboard page or triggers unwanted browser zooming.
- **Prevention:** Use `e.preventDefault()` inside non-passive wheel listeners on the canvas, or set `overscroll-behavior: contain; touch-action: none;` on the graph container.

## 2. React 19 Peer Dependency Collisions
- **Pitfall:** Attempting to install `reactflow` (v11) in React 19 triggers `ERESOLVE unable to resolve dependency tree` errors due to peer requirement of React 18.
- **Prevention:** Use our native React 19 SVG architecture which has 0 external dependencies and builds instantaneously with Vite in <900ms.

## 3. High Node Count Canvas Sluggishness
- **Pitfall:** Uncontrolled re-renders during mousemove pan operations re-rendering every node sub-component 60 times a second.
- **Prevention:** Apply pan/zoom transform strictly to an outer `<g transform="...">` container via CSS or direct transform attribute, isolating child node elements from unnecessary state recalculations.

## 4. Dark & Light Theme Desynchronization
- **Pitfall:** Hardcoding hex colors (`#ffffff`, `#0f172a`) in SVG strokes or fills, resulting in invisible text or lines when users toggle between Sun and Moon modes.
- **Prevention:** Bind all SVG fills, strokes, and gradients to existing CSS custom properties (`var(--card-border)`, `var(--text-primary)`, `var(--bg-secondary)`).

## 5. Label Overlap & Node Collision
- **Pitfall:** In networks with multiple devices per tier, nodes overlap or text truncates unreadably.
- **Prevention:** Enforce min-gap bounds (minimum 240px horizontal step per node), with horizontal canvas expansion and smooth scroll/pan support.
