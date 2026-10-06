import { useEffect, useState } from "react";
import { searchLocation } from "../services/nominatim";
import "./SearchBar.css";

export default function SearchBar({ onSelectPlace }) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [loadingQuery, setLoadingQuery] = useState(null);
  const [suggestionQuery, setSuggestionQuery] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (query.trim().length < 3) {
      return undefined;
    }
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setLoadingQuery(query);
      setError("");
      try {
        const places = await searchLocation(query, controller.signal);
        if (!controller.signal.aborted) {
          setSuggestions(places);
          setSuggestionQuery(query);
          setError(places.length ? "" : "No locations found. Try a nearby city or different spelling.");
        }
      } catch {
        if (!controller.signal.aborted) setError("Place search is temporarily unavailable.");
      } finally {
        if (!controller.signal.aborted) setLoadingQuery((current) => current === query ? null : current);
      }
    }, 350);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  function choosePlace(place) {
    onSelectPlace({ lat: Number(place.lat), lon: Number(place.lon), name: place.display_name });
    setQuery(place.display_name);
    setSuggestions([]);
    setSuggestionQuery("");
    setError("");
  }

  function handleSubmit(event) {
    event.preventDefault();
    if (suggestionQuery === query && suggestions.length) choosePlace(suggestions[0]);
    else if (query.trim().length < 3) setError("Enter at least 3 characters to search.");
    else if (loadingQuery !== query && suggestionQuery !== query) setError("Choose a matching place from the suggestions.");
  }

  return (
    <form className="place-search" onSubmit={handleSubmit} role="search">
      <label className="sr-only" htmlFor="place-search-input">Search for a location</label>
      <span className="search-symbol" aria-hidden="true">⌕</span>
      <input id="place-search-input" type="search" value={query} onChange={(event) => { setError(""); setQuery(event.target.value); }} placeholder="Search a city or address" autoComplete="off" aria-expanded={suggestions.length > 0} aria-controls="place-suggestions" />
      <button type="submit" aria-label="Select first matching place" disabled={loadingQuery === query || query.trim().length < 3}>{loadingQuery === query ? <span className="spinner spinner-dark" /> : "Search"}</button>
      {query.trim().length >= 3 && suggestionQuery === query && suggestions.length > 0 && <div className="place-suggestions" id="place-suggestions" role="listbox">
        {suggestions.map((place) => <button type="button" role="option" className="place-suggestion" key={place.id} onClick={() => choosePlace(place)}>
          <span className="suggestion-pin" aria-hidden="true">⌖</span><span>{place.display_name}</span>
        </button>)}
      </div>}
      {error && <span className="search-message" role="status">{error}</span>}
    </form>
  );
}
