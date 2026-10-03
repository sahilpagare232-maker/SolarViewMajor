
import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";

function DrawControl({
  drawingMode,
  setDrawingMode,
  onAreaSelect,
}) {
  const map = useMap();

  const startPoint = useRef(null);
  const rectangle = useRef(null);
  const isDrawing = useRef(false);

  useEffect(() => {
    function onMouseDown(e) {
      if (!drawingMode) return;

      isDrawing.current = true;
      startPoint.current = e.latlng;

      // Disable map dragging while selecting
      map.dragging.disable();

      // Remove previous rectangle
      if (rectangle.current) {
        map.removeLayer(rectangle.current);
        rectangle.current = null;
      }
    }

    function onMouseMove(e) {
      if (!drawingMode || !isDrawing.current) return;

      const bounds = L.latLngBounds(
        startPoint.current,
        e.latlng
      );

      if (!rectangle.current) {
        rectangle.current = L.rectangle(bounds, {
          color: "#3388ff",
          weight: 2,
          fillOpacity: 0.2,
        }).addTo(map);
      } else {
        rectangle.current.setBounds(bounds);
      }
    }

    function onMouseUp(e) {
      if (!isDrawing.current) return;

      isDrawing.current = false;

      // Enable map dragging again
      map.dragging.enable();

      const bounds = L.latLngBounds(
        startPoint.current,
        e.latlng
      );

      const sw = bounds.getSouthWest();
      const ne = bounds.getNorthEast();

      const area = {
        sw_lat: sw.lat,
        sw_lng: sw.lng,
        ne_lat: ne.lat,
        ne_lng: ne.lng,
      };

      

      // Send selected area to Map.jsx
      if (onAreaSelect) {
        onAreaSelect(area);
      }

      // Stop drawing mode
      setDrawingMode(false);

      startPoint.current = null;
    }

    map.on("mousedown", onMouseDown);
    map.on("mousemove", onMouseMove);
    map.on("mouseup", onMouseUp);

    return () => {
      map.off("mousedown", onMouseDown);
      map.off("mousemove", onMouseMove);
      map.off("mouseup", onMouseUp);
    };
  }, [map, drawingMode, setDrawingMode, onAreaSelect]);

  return null;
}

export default DrawControl;