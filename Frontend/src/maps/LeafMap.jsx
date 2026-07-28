import { MapContainer, TileLayer, useMap } from "react-leaflet";
import { useEffect } from "react";

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

function LeafMap({ selectedPlace }) {
  return (
    <MapContainer
      center={[19.0760, 72.8777]}
      zoom={16}
      style={{ height: "50vh", width: "50%" }}
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

      {/* Move map when a place is selected */}
      {selectedPlace && <MapUpdater place={selectedPlace} />}
    </MapContainer>
  );
}

export default LeafMap;