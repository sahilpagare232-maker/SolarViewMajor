import { useNavigate } from "react-router-dom";
import LeafMap from "../maps/LeafMap";
import SearchBar from "../maps/SearchBar";
function Map() {
    const navigate =useNavigate();
  return (
    <div>
      <h1>Map Page</h1>
      <SearchBar />
      < LeafMap/>
      <button onClick={()=>navigate("/view")}>View</button>
    </div>
  );
}

export default Map;