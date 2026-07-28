import { useNavigate } from "react-router-dom";
import { useState } from "react";
import LeafMap from "../maps/LeafMap";
import SearchBar from "../maps/SearchBar";
function Map() {
    const navigate =useNavigate();
    const [selectedPlace, setSelectedPlace] = useState(null);
  return (
    <div>
      <h1>Map Page</h1>
      <SearchBar onSelectPlace={setSelectedPlace}/>
      < LeafMap  selectedPlace={selectedPlace}/>
      <button onClick={()=>navigate("/view")}>View</button>
    </div>
  );
}

export default Map;