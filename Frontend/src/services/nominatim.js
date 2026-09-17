// src/services/searchService.js

const BASE_URL = "https://photon.komoot.io/api/";

export async function searchLocation(query,signal) {
  if (!query.trim()) return [];

  const url = `${BASE_URL}?q=${encodeURIComponent(query)}&limit=5`;

  const response = await fetch(url,{signal,});

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const data = await response.json();

  return data.features.map((feature, index) => {
    const properties = feature.properties;
    const coordinates = feature.geometry.coordinates;

    return {
      id: `${properties.osm_type || "unknown"}-${properties.osm_id || "unknown"}-${index}`,

      lat: coordinates[1],
      lon: coordinates[0],

      name: properties.name || "Unknown",
      city: properties.city || "",
      state: properties.state || "",
      country: properties.country || "",

      display_name: [
        properties.name,
        properties.city,
        properties.state,
        properties.country,
      ]
        .filter(Boolean)
        .join(", "),
    };
  });
}