import { useState } from "react";
import {
  Cartesian3,
  HeadingPitchRange,
  Math as CesiumMath,
  Rectangle,
} from "cesium";

const VIEWS = [
  { label: "Top View", heading: 0, pitch: -90 },
  { label: "North View", heading: 0, pitch: -35 },
  { label: "East View", heading: 90, pitch: -35 },
  { label: "South View", heading: 180, pitch: -35 },
  { label: "West View", heading: 270, pitch: -35 },
];

export default function CameraControls({ viewerRef, area }) {
  const [currentView, setCurrentView] = useState("Top View");

  function getViewer() {
    const viewer = viewerRef.current;
    return viewer && !viewer.isDestroyed() ? viewer : null;
  }

  function getAreaCenter() {
    if (!area) return null;

    const rectangle = Rectangle.fromDegrees(
      area.sw_lng,
      area.sw_lat,
      area.ne_lng,
      area.ne_lat
    );

    const center = Rectangle.center(rectangle);
    return Cartesian3.fromRadians(center.longitude, center.latitude, 0);
  }

  function getRange() {
    if (!area) return 500;

    const width =
      Math.abs(area.ne_lng - area.sw_lng) *
      111320 *
      Math.cos(((area.sw_lat + area.ne_lat) / 2) * Math.PI / 180);

    const height = Math.abs(area.ne_lat - area.sw_lat) * 111320;

    return Math.max(width, height, 100) * 1.2;
  }

  function setView(view) {
    const viewer = getViewer();
    const center = getAreaCenter();
    if (!viewer || !center) return;

    viewer.camera.lookAt(
      center,
      new HeadingPitchRange(
        CesiumMath.toRadians(view.heading),
        CesiumMath.toRadians(view.pitch),
        getRange()
      )
    );

    setCurrentView(view.label);
  }

  function rotate(direction) {
    const viewer = getViewer();
    const center = getAreaCenter();
    if (!viewer || !center) return;

    // Orbit the camera around the area's center.
    const step = CesiumMath.toRadians(15) * direction;
    const offset = Cartesian3.subtract(
      viewer.camera.positionWC,
      center,
      new Cartesian3()
    );

    const range = Cartesian3.magnitude(offset);
    const cartographic = viewer.camera.positionCartographic;

    const heading = cartographic
      ? viewer.camera.heading + step
      : step;

    viewer.camera.lookAt(
      center,
      new HeadingPitchRange(
        heading,
        viewer.camera.pitch,
        Math.max(range, getRange())
      )
    );
  }



  return (
    <section
      aria-label="3D camera controls"
      style={{
        position: "absolute",
        top: 16,
        right: 16,
        zIndex: 2,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        padding: 12,
        borderRadius: 12,
        background: "white",
        boxShadow: "0 2px 12px #0002",
        color: "#182820",
      }}
    >
      <strong style={{ fontSize: 13 }}>3D Controls</strong>

      <div style={{ display: "flex", gap: 6 }}>
        <button
          className="button button-secondary"
          onClick={() => rotate(-1)}
          title="Orbit left"
        >
          ↶ Left
        </button>
        <button
          className="button button-secondary"
          onClick={() => rotate(1)}
          title="Orbit right"
        >
          Right ↷
        </button>
      </div>

      <div style={{ display: "flex", gap: 6 }}>
        <button
          className="button button-secondary"
          onClick={() => getViewer()?.camera.zoomIn(getRange() * 0.2)}
        >
          Zoom +
        </button>
        <button
          className="button button-secondary"
          onClick={() => getViewer()?.camera.zoomOut(getRange() * 0.2)}
        >
          Zoom −
        </button>
      </div>

      <button
  className="button button-primary"
  onClick={() => {
    const currentIndex = VIEWS.findIndex(
      (view) => view.label === currentView
    );

    const nextView = VIEWS[
      (currentIndex + 1) % VIEWS.length
    ];

    setView(nextView);
  }}
  title="Switch camera view"
>
  View: {currentView} ↻
</button>

    </section>
  );
}