import { GeoJSON, MapContainer, Rectangle, TileLayer, useMap } from "react-leaflet";
import { useEffect } from "react";
import DrawControl from "./DrawControl";
import './LeafMap.css'

function MapUpdater({ place }) {
  const map = useMap();

  useEffect(() => {
    if (place) {
      map.setView([place.lat, place.lon], 18, {
        animate: true,
      });
    }
  }, [place, map]);

  return null;
}

function LeafMap({ selectedPlace, selectedArea, analysis, onAreaSelect, drawingMode, setDrawingMode }) {
  const panelLayouts = analysis?.optimization?.buildings ?? [];
  const analysisKey = `${analysis?.area?.sw_lat ?? ""}-${analysis?.area?.sw_lng ?? ""}-${analysis?.area?.ne_lat ?? ""}-${analysis?.area?.ne_lng ?? ""}`;
  return (
    <MapContainer
      className={`LeafMap${drawingMode ? " is-drawing" : ""}`}
      center={[19.0760, 72.8777]}
      zoom={16}
      scrollWheelZoom
    >
      <TileLayer attribution={'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'} url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

      {selectedPlace && <MapUpdater place={selectedPlace} />}

      <DrawControl
      drawingMode={drawingMode}
      setDrawingMode={setDrawingMode}
      onAreaSelect={onAreaSelect}
      />
      {selectedArea && <Rectangle bounds={[[selectedArea.sw_lat, selectedArea.sw_lng], [selectedArea.ne_lat, selectedArea.ne_lng]]} pathOptions={{ color: "#347bc2", weight: 2, dashArray: "6 5", fillOpacity: 0.025 }} />}
      {analysis?.buildings?.geojson?.features?.length > 0 && <GeoJSON
        key={`building-${analysisKey}`}
        data={analysis.buildings.geojson}
        style={{ color: "#147d69", weight: 2, fillColor: "#27b394", fillOpacity: 0.26 }}
        onEachFeature={(feature, layer) => {
          const popup = document.createElement("div");
          const title = document.createElement("strong");
          title.textContent = feature.properties?.building_type || "Building";
          popup.append(title);
          const area = feature.properties?.area_m2;
          if (Number.isFinite(area)) {
            popup.append(document.createElement("br"), document.createTextNode(`${area.toLocaleString()} m² footprint`));
          }
          layer.bindPopup(popup);
        }}
      />}
      {panelLayouts.map((building) => building.panel_layout?.features?.length > 0 && <GeoJSON
        key={`panels-${analysisKey}-${building.building_id}`}
        data={building.panel_layout}
        style={{ color: "#aa6b05", weight: 1, fillColor: "#f7b733", fillOpacity: 0.85 }}
        onEachFeature={(feature, layer) => layer.bindPopup(`Panel ${feature.properties?.panel_number ?? ""} · ${feature.properties?.rated_power_w ?? ""} W`)}
      />)}
    </MapContainer>
  );
}

export default LeafMap;
