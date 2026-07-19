const BASE_URL = "https://nominatim.openstreetmap.org/search";

export async function searchLocation(query) {
  if (!query.trim()) {
    throw new Error("Search query is empty");
  }

  const url = `${BASE_URL}?q=${encodeURIComponent(
    query
  )}&format=jsonv2&limit=1`;

  const response = await fetch(url, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error("Failed to fetch location");
  }

  const data = await response.json();

  return data;
}