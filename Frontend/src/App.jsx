import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Map from "./pages/Map";
import Viewer from "./pages/Viewer";
const CesiumViewer = lazy(() => import("./pages/cesuimViewer"));

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/map" element={<Map />} />
      <Route path="/view" element={<Viewer />} />
      <Route path="/cesium-viewer" element={<Suspense fallback={<main className="solar-page empty-view"><div className="empty-card"><span className="spinner spinner-dark" /> Loading 3D viewer…</div></main>}><CesiumViewer /></Suspense>} />
    </Routes>
  );
}

export default App;
