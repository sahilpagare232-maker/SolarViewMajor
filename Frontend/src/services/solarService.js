// src/services/solarService.js

import apiFetch from "./api";

// Run the full area analysis using the existing frontend bounding-box format.
export const sendArea = (selectedArea) => {
  return apiFetch("/api/analyze-area", {
    method: "POST",
    body: JSON.stringify({
      coordinates: selectedArea,
    }),
  });
};

// Optimize only the building selected in the Cesium scene.
export const optimizeBuilding = (building) => apiFetch("/api/optimize-building", {
  method: "POST",
  body: JSON.stringify(building),
});
