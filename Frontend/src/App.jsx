import { Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Map from "./pages/Map";
import Viewer from "./pages/Viewer";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/map" element={<Map />} />
      <Route path="/view" element={<Viewer />} />
    </Routes>
  );
}

export default App;