// src/services/solarService.js

import apiFetch from "./api";

// Run the full area analysis using the existing frontend bounding-box format.
export const sendArea = (selectedArea, { includeOptimization = true } = {}) => {
  console.log("Sending area for analysis:", selectedArea, "Include optimization:", includeOptimization);
  return apiFetch("/api/analyze-area", {
    method: "POST",
    body: JSON.stringify({
      coordinates: selectedArea,
      include_optimization: includeOptimization,
    }),
  });
};

// Optimize only the building selected in the Cesium scene.
export const optimizeBuilding = (building) => apiFetch("/api/optimize-building", {
  method: "POST",
  body: JSON.stringify(building),
});
