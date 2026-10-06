import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";

export default function DrawControl({ drawingMode, setDrawingMode, onAreaSelect }) {
  const map = useMap();
  const startPoint = useRef(null);
  const rectangle = useRef(null);
  const activePointer = useRef(null);

  useEffect(() => {
    const container = map.getContainer();

    function finishDrawing(event, cancelled = false) {
      if (activePointer.current !== event.pointerId) return;
      activePointer.current = null;
      if (map.dragging.enabled() === false) map.dragging.enable();
      if (cancelled) {
        startPoint.current = null;
        return;
      }
      const endPoint = map.mouseEventToLatLng(event);
      const bounds = L.latLngBounds(startPoint.current, endPoint);
      const southWest = bounds.getSouthWest();
      const northEast = bounds.getNorthEast();
      startPoint.current = null;
      if (southWest.lat !== northEast.lat && southWest.lng !== northEast.lng) {
        onAreaSelect?.({ sw_lat: southWest.lat, sw_lng: southWest.lng, ne_lat: northEast.lat, ne_lng: northEast.lng });
      }
      setDrawingMode(false);
    }

    function handlePointerDown(event) {
      if (!drawingMode || (event.pointerType === "mouse" && event.button !== 0)) return;
      if (event.target instanceof Element && event.target.closest(".leaflet-control, .leaflet-popup")) return;
      event.preventDefault();
      activePointer.current = event.pointerId;
      startPoint.current = map.mouseEventToLatLng(event);
      map.dragging.disable();
      if (rectangle.current) map.removeLayer(rectangle.current);
      rectangle.current = null;
      try { container.setPointerCapture(event.pointerId); } catch { /* Pointer capture is optional. */ }
    }

    function handlePointerMove(event) {
      if (!drawingMode || activePointer.current !== event.pointerId || !startPoint.current) return;
      event.preventDefault();
      const bounds = L.latLngBounds(startPoint.current, map.mouseEventToLatLng(event));
      if (!rectangle.current) rectangle.current = L.rectangle(bounds, { color: "#347bc2", weight: 2, fillOpacity: 0.12 }).addTo(map);
      else rectangle.current.setBounds(bounds);
    }

    function handlePointerUp(event) { finishDrawing(event); }
    function handlePointerCancel(event) { finishDrawing(event, true); }

    container.addEventListener("pointerdown", handlePointerDown);
    container.addEventListener("pointermove", handlePointerMove);
    container.addEventListener("pointerup", handlePointerUp);
    container.addEventListener("pointercancel", handlePointerCancel);
    return () => {
      container.removeEventListener("pointerdown", handlePointerDown);
      container.removeEventListener("pointermove", handlePointerMove);
      container.removeEventListener("pointerup", handlePointerUp);
      container.removeEventListener("pointercancel", handlePointerCancel);
      if (activePointer.current !== null && map.dragging.enabled() === false) map.dragging.enable();
      activePointer.current = null;
    };
  }, [map, drawingMode, setDrawingMode, onAreaSelect]);

  return null;
}
