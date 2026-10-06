import { useMemo } from "react";
import { Link, useLocation } from "react-router-dom";
import LeafMap from "../maps/LeafMap";
import "./SolarView.css";

function readSavedAnalysis() {
  try {
    const saved = sessionStorage.getItem("solarview-analysis");
    return saved ? JSON.parse(saved) : null;
  } catch {
    return null;
  }
}

function MetricCard({ label, value, detail }) {
  return <article className="metric-card"><span>{label}</span><strong>{value}</strong><small>{detail}</small></article>;
}

export default function Viewer() {
  const { state } = useLocation();
  const stored = useMemo(() => readSavedAnalysis(), []);
  const analysis = state?.analysis ?? stored;
  if (!analysis) return <main className="solar-page empty-view"><div className="empty-card"><span className="empty-icon">⌖</span><p className="eyebrow">NO ANALYSIS YET</p><h1>Select an area to get started</h1><p className="muted">Choose a location, draw an area on the map, and run a solar analysis to see buildings and panel placements here.</p><Link className="button button-primary" to="/map">Go to area selection →</Link></div></main>;

  const area = analysis.area;
  const buildings = analysis.buildings?.items ?? [];
  const optimization = analysis.optimization ?? {};
  const panelLayouts = optimization.buildings ?? [];
  const place = { lat: (area.sw_lat + area.ne_lat) / 2, lon: (area.sw_lng + area.ne_lng) / 2, name: "Analyzed area" };
  const energyClass = analysis.solar?.data_class ?? "Estimated energy output";

  return <main className="solar-page results-page">
    <header className="topbar">
      <Link className="brand" to="/" aria-label="SolarView home"><span className="brand-mark">☀</span> SolarView</Link>
      <Link className="button button-secondary compact-button" to="/map">＋ New analysis</Link>
    </header>

    <section className="results-heading">
      <div><p className="eyebrow">SOLAR ANALYSIS</p><h1>Your area at a glance</h1><p className="muted">Buildings from OpenStreetMap · Estimated energy from demo solar data</p></div>
      <span className="data-badge">◉ {analysis.solar?.irradiance_source === "synthetic_demo" ? "DEMO SOLAR DATA" : "ESTIMATED"}</span>
    </section>

    <section className="metric-grid" aria-label="Analysis summary">
      <MetricCard label="Buildings found" value={buildings.length.toLocaleString()} detail="OpenStreetMap footprints" />
      <MetricCard label="Panels placed" value={(optimization.total_panels ?? 0).toLocaleString()} detail="Grid packed on usable roof area" />
      <MetricCard label="Installed capacity" value={`${Number(optimization.installed_capacity_kw ?? 0).toLocaleString()} kW`} detail="Based on configured panel rating" />
      <MetricCard label="Annual energy" value={`${Number(optimization.annual_energy_kwh ?? 0).toLocaleString()} kWh`} detail={energyClass} />
    </section>

    <section className="results-map-card">
      <div className="section-heading"><div><h2>Buildings & panel layout</h2><p>Green outlines show buildings. Gold rectangles show proposed panels.</p></div><div className="map-legend"><span><i className="legend-building" /> Buildings</span><span><i className="legend-panel" /> Panels</span></div></div>
      <LeafMap selectedPlace={place} selectedArea={area} analysis={analysis} onAreaSelect={() => {}} drawingMode={false} setDrawingMode={() => {}} />
    </section>

    <section className="building-section">
      <div className="section-heading"><div><h2>Building estimates</h2><p>Usable roof is approximated from each footprint with a setback.</p></div><span className="count-pill">{buildings.length} {buildings.length === 1 ? "building" : "buildings"}</span></div>
      {buildings.length === 0 ? <div className="empty-table">No building footprints were returned for this area.</div> : <div className="table-wrap"><table>
        <thead><tr><th>Building</th><th>Footprint area</th><th>Usable roof</th><th>Height</th><th>Panels</th><th>Annual energy</th></tr></thead>
        <tbody>{buildings.map((building) => {
          const result = panelLayouts.find((item) => item.building_id === building.building_id);
          return <tr key={building.building_id}><td><strong>{building.building_type || "Building"}</strong><small>{building.building_id}</small></td><td>{Number(building.area_m2).toLocaleString()} m²</td><td>{Number(building.usable_roof_area_m2 ?? 0).toLocaleString()} m²</td><td>{building.height == null ? "—" : `${building.height} m`}</td><td>{(result?.panel_count ?? 0).toLocaleString()}</td><td>{Number(result?.annual_energy_kwh ?? 0).toLocaleString()} kWh</td></tr>;
        })}</tbody>
      </table></div>}
    </section>

    <footer className="results-footnote">{analysis.solar?.data_class || "Energy is estimated from synthetic demo irradiance, not measured weather."} Rooftop usability is an approximation; roof pitch, shade and obstructions are not modeled.</footer>
  </main>;
}
