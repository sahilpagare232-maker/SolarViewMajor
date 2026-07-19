import { useNavigate } from "react-router-dom";

export default function Viewer() {
    const navigate = useNavigate();
  return (
    <div>
        3D model
        <button onClick={()=>navigate("/map")}>New Analysis</button>
    </div>
  )
}
