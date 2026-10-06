// src/services/api.js

const apiFetch = async (endpoint, options = {}) => {
  let response;
  try {
    response = await fetch(endpoint, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error("Can’t reach the SolarView backend. Make sure it is running at http://127.0.0.1:8000.", { cause: error });
  }

  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try {
      const body = await response.json();
      const detail = body.detail;
      if (typeof detail === "string") message = detail;
      else if (Array.isArray(detail)) message = detail.map((issue) => issue.msg).filter(Boolean).join(" ") || message;
    } catch {
      // Keep the HTTP status message when the error body is not JSON.
    }
    throw new Error(message);
  }

  return response.json();
};

export default apiFetch;
