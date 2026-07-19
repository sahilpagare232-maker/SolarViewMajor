import { MapContainer, TileLayer } from "react-leaflet";

function LeafMap() {
  return (
    <MapContainer
      center={[19.0760, 72.8777]}
      zoom={16}
      minZoom={15}
      maxZoom={20}
      style={{ height: "50vh", width: "50%" }}
    >
      <TileLayer
       
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
    </MapContainer>
  );
}

export default LeafMap;