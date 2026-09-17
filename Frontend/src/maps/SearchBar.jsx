import React, { useState , useEffect } from 'react';
import "./SearchBar.css"
import { searchLocation } from '../services/nominatim';

const SearchBar = ({onSelectPlace}) => {
  const [address, setAddress] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isSelecting, setIsSelecting] = useState(false);
  
  useEffect(() => {
    if (isSelecting) return;
  // Clear suggestions if input is too short
  if (address.trim().length < 3) {
    setSuggestions([]);
    return;
  }
   const controller = new AbortController();

  // Wait 400ms after user stops typing
  const timer = setTimeout(async () => {
    try {
      const results = await searchLocation(address,controller.signal);
      // Only update suggestions if this request wasn't cancelled
      if (!controller.signal.aborted) {
        setSuggestions(results);
      }
    } catch (error) {
      if (error.name !== "AbortError") {
        console.error("Suggestion fetch failed:", error);
      }
    }
  }, 400);

  return () => {
    clearTimeout(timer);
     controller.abort();
  };
}, [address,isSelecting]);
  const [loading, setLoading] = useState(false);
  const handleSearch = async () => {
    try {
      const result = await searchLocation(address);

      console.log('Nominatim result:', result);

      if (result.length > 0) {
        const place = result[0];

        console.log({
          lat: parseFloat(place.lat),
          lon: parseFloat(place.lon),
          name: place.display_name,
        });
      } else {
        console.log('No location found');
      }
    } catch (error) {
      console.error('Search failed:', error);
    }
  };  
  return (
      <div>
        <div className="grid" />
        <div id="poda">
          <div className="glow" />
          <div className="darkBorderBg" />
          <div className="darkBorderBg" />
          <div className="darkBorderBg" />
          <div className="white" />
          <div className="border" />
          <div id="main">
            <input
            placeholder="Search address..."
  type="text"
  name="text"
  className="input"
  value={address}
onChange={async (e) => {
  const value = e.target.value;
  setAddress(value);

  // If input is empty, clear suggestions and stop
  if (!value.trim()) {
    setSuggestions([]);
    return;
  }

  // Optional: wait until at least 3 characters
  if (value.length < 3) {
    setSuggestions([]);
    return;
  }

 
}}
  onKeyDown={(e) => {
    if (e.key === 'Enter') handleSearch();
  }}
            />
            {suggestions.length > 0 && (
  <div className="suggestions">
    {suggestions.map((place) => (

      <div
        key={place.id}
        className="suggestion-item"
        onMouseDown={() => {
          setIsSelecting(true);
  const selectedPlace = {
    lat: parseFloat(place.lat),
    lon: parseFloat(place.lon),
    name: place.display_name,
  };

  setAddress(place.display_name);
  setSuggestions([]);

  console.log(selectedPlace);

  // send coordinates to parent (Map.jsx)
  onSelectPlace(selectedPlace);
  setTimeout(() => setIsSelecting(false), 0);
}}
      >
        <div className="place-name">
          {place.display_name}
        </div>
      </div>
    ))}
  </div>
)}
            <div id="input-mask" />
            <div id="pink-mask" />

            <div id="search-icon" onClick={handleSearch}>
              <svg xmlns="http://www.w3.org/2000/svg" width={24} viewBox="0 0 24 24" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" height={24} fill="none" className="feather feather-search">
                <circle stroke="url(#search)" r={8} cy={11} cx={11} />
                <line stroke="url(#searchl)" y2="16.65" y1={22} x2="16.65" x1={22} />
                <defs>
                  <linearGradient gradientTransform="rotate(50)" id="search">
                    <stop stopColor="#f8e7f8" offset="0%" />
                    <stop stopColor="#b6a9b7" offset="50%" />
                  </linearGradient>
                  <linearGradient id="searchl">
                    <stop stopColor="#b6a9b7" offset="0%" />
                    <stop stopColor="#837484" offset="50%" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>
        </div>
      </div>
  );
}

export default SearchBar