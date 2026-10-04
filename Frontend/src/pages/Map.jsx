  import { useNavigate } from "react-router-dom";
  import { useState } from "react";
  import LeafMap from "../maps/LeafMap";
  import SearchBar from "../maps/SearchBar";
  import { sendArea } from "../services/solarService";


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
    const handleView = async () => {
  try {
    const response = await sendArea(selectedArea);

    console.log("Area sent:", response);

    navigate("/view");
  } catch (error) {
    console.error("Failed to send area:", error);
  }
};


    return (
      <div className="map-page">
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
        <button onClick={handleView}>View</button>
      </div>
    );
  }

  export default Map; 