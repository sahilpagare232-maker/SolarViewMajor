  import { useNavigate } from "react-router-dom";
  import { useState } from "react";
  import LeafMap from "../maps/LeafMap";
  import SearchBar from "../maps/SearchBar";

  function Map() {
    const navigate = useNavigate();

    const [selectedPlace, setSelectedPlace] = useState(null);
    const [selectedArea, setSelectedArea] = useState(null);
    const [drawingMode, setDrawingMode] = useState(false);

    function handlePlaceSelect(place){
      //Set the new location 
      setSelectedPlace(place); 
      // Reset previously selected area 
      setSelectedArea(null); 
      // Make sure drawing mode is stopped 
      setDrawingMode(false); 
    }

    return (
      <div>
        <h1>Map Page</h1>

        <SearchBar onSelectPlace={handlePlaceSelect} />

        <LeafMap
          selectedPlace={selectedPlace}
          onAreaSelect={setSelectedArea}
          drawingMode={drawingMode}
          setDrawingMode={setDrawingMode}
        />
        <button onClick={() =>{ 
    
          setDrawingMode(true)}}>{selectedArea ? "Select New Area" : "Select Area"}</button>
        <button onClick={() => navigate("/view")}>View</button>
      </div>
    );
  }

  export default Map; 