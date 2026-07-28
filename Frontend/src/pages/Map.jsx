import { useNavigate } from "react-router-dom";
import { useState } from "react";
import LeafMap from "../maps/LeafMap";
import SearchBar from "../maps/SearchBar";

function Map() {
  const navigate = useNavigate();

  const [selectedPlace, setSelectedPlace] = useState(null);
  const [selectedArea, setSelectedArea] = useState(null);
  const [drawingMode, setDrawingMode] = useState(false);
  return (
    <div>
      <h1>Map Page</h1>

      <SearchBar onSelectPlace={setSelectedPlace} />

      <LeafMap
        selectedPlace={selectedPlace}
        onAreaSelect={setSelectedArea}
        drawingMode={drawingMode}
        setDrawingMode={setDrawingMode}
      />
      <button onClick={() =>{ 
   
        setDrawingMode(true)}}>Select Area</button>
      <button onClick={() => navigate("/view")}>View</button>
    </div>
  );
}

export default Map; 