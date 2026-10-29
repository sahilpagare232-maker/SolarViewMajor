import { Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Map from "./pages/Map";
import Viewer from "./pages/Viewer";
import CesiumViewer from "./pages/cesuimViewer";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/map" element={<Map />} />
      <Route path="/view" element={<Viewer />} />
      <Route path="/cesium-viewer" element={<CesiumViewer />} />
    </Routes>
  );
}

export default App;