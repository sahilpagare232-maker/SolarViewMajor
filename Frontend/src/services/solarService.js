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
