import { MapContainer, TileLayer, useMap } from "react-leaflet";
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

function LeafMap({ selectedPlace, onAreaSelect, drawingMode,setDrawingMode }) {
  return (
    <MapContainer
      className="LeafMap"
      center={[19.0760, 72.8777]}
      zoom={16}
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

      {selectedPlace && <MapUpdater place={selectedPlace} />}

      <DrawControl
      drawingMode={drawingMode}
      setDrawingMode={setDrawingMode}
      onAreaSelect={onAreaSelect}
      />
    </MapContainer>
  );
}

export default LeafMap;