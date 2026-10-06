import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import LeafMap from "../maps/LeafMap";
import SearchBar from "../maps/SearchBar";
import { sendArea } from "../services/solarService";
import "./SolarView.css";

const DEFAULT_PLACE = { lat: 19.076, lon: 72.8777, name: "Mumbai, India" };

function MapPage() {
  const navigate = useNavigate();
  const [selectedPlace, setSelectedPlace] = useState(DEFAULT_PLACE);
  const [selectedArea, setSelectedArea] = useState(null);
  const [drawingMode, setDrawingMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handlePlaceSelect(place) {
    setSelectedPlace(place);
    setSelectedArea(null);
    setDrawingMode(false);
    setError("");
  }

  async function handleAnalyze() {
    if (!selectedArea || loading) return;
    setLoading(true);
    setError("");
    try {
      const analysis = await sendArea(selectedArea);
      try { sessionStorage.setItem("solarview-analysis", JSON.stringify(analysis)); } catch { /* Route state still carries the result. */ }
      navigate("/view", { state: { analysis } });
    } catch (requestError) {
      setError(requestError.message || "Analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="solar-page map-page-shell">
      <header className="topbar">
        <Link className="brand" to="/" aria-label="SolarView home"><span className="brand-mark">☀</span> SolarView</Link>
        <span className="topbar-note">Rooftop solar potential</span>
      </header>

      <section className="map-heading">
        <div>
          <p className="eyebrow">AREA ANALYSIS</p>
          <h1>Choose a location and rooftop area</h1>
          <p className="muted">Search for a place, draw a rectangle around the buildings, and run the analysis.</p>
        </div>
        <SearchBar onSelectPlace={handlePlaceSelect} />
      </section>

      <section className="map-card" aria-label="Area selection map">
        <LeafMap selectedPlace={selectedPlace} selectedArea={selectedArea} onAreaSelect={(area) => { setSelectedArea(area); setError(""); }} drawingMode={drawingMode} setDrawingMode={setDrawingMode} />
        <div className="map-overlay"><span className="map-dot" /> OpenStreetMap</div>
      </section>

      <section className="selection-bar">
        <div className="selection-copy" aria-live="polite">
          <span className={`status-indicator ${selectedArea ? "is-ready" : ""}`} />
          <div><strong>{selectedArea ? "Area selected" : "No area selected"}</strong>
            <span>{selectedArea ? `${selectedArea.sw_lat.toFixed(5)}, ${selectedArea.sw_lng.toFixed(5)} — ${selectedArea.ne_lat.toFixed(5)}, ${selectedArea.ne_lng.toFixed(5)}` : "Use the button to draw a rectangle on the map."}</span>
          </div>
        </div>
        <div className="selection-actions">
          <button className="button button-secondary" type="button" onClick={() => setDrawingMode(true)} disabled={loading}>
            {drawingMode ? "Drag on map to select…" : selectedArea ? "Redraw area" : "＋ Select area"}
          </button>
          <button className="button button-primary" type="button" onClick={handleAnalyze} disabled={!selectedArea || loading}>
            {loading ? <><span className="spinner" /> Analyzing area…</> : "Analyze solar potential →"}
          </button>
        </div>
      </section>
      {error && <div className="alert-error" role="alert"><strong>Couldn’t complete the analysis.</strong> {error}</div>}
      <p className="map-footnote">Building data comes from OpenStreetMap. Solar output is an estimate using demo irradiance data.</p>
    </main>
  );
}

export default MapPage;
