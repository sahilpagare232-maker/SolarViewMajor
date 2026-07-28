const BASE_URL = "https://nominatim.openstreetmap.org/search";

// src/services/searchService.js

export async function searchLocation(query) {
  if (!query.trim()) return [];

  const url =
    `https://photon.komoot.io/api/?q=${encodeURIComponent(query)}&limit=5`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const data = await response.json();

  // Normalize the response so the rest of your app stays the same
  return data.features.map((feature) => ({
    id: feature.properties.osm_id,
    lat: feature.geometry.coordinates[1],
    lon: feature.geometry.coordinates[0],
    name: feature.properties.name || "Unknown",
    city: feature.properties.city || "",
    state: feature.properties.state || "",
    country: feature.properties.country || "",
    display_name: [
      feature.properties.name,
      feature.properties.city,
      feature.properties.state,
      feature.properties.country,
    ]
      .filter(Boolean)
      .join(', '),
  }));
}