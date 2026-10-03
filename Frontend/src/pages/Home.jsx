import { useNavigate } from "react-router-dom";

function Home() {
  const navigate = useNavigate();
  
  return (
    <div>
      <h1>SolarView</h1>

      <button onClick={() => navigate("/map")}>
        Start Analysis
      </button>
    </div>
  );
}

export default Home;