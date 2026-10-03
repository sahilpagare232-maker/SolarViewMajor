// src/services/solarService.js

import apiFetch from "./api";

// POST
export const sendArea = (selectedArea) => {
  return apiFetch("/api/area", {
    method: "POST",
    body: JSON.stringify({
      coordinates: selectedArea,
    }),
  });
};

// GET
export const getSolarData = () => {
  return apiFetch("/api/solar");
};