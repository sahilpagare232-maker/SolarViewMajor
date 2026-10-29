
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import {
  Viewer,
  GeoJsonDataSource,
  Color,
  HeightReference,
  Matrix4,
  Rectangle
} from "cesium";

import "cesium/Build/Cesium/Widgets/widgets.css";

const DEFAULT_DISPLAY_HEIGHT_M = 10;

function readSavedAnalysis() {
  try {
    const saved = sessionStorage.getItem("solarview-analysis");
    return saved ? JSON.parse(saved) : null;
  } catch {
    return null;
  }
}

function isValidPosition(position) {
  return Array.isArray(position)
    && position.length >= 2
    && Number.isFinite(position[0])
    && Number.isFinite(position[1])
    && position.slice(2).every(Number.isFinite)
    && position[0] >= -180
    && position[0] <= 180
    && position[1] >= -90
    && position[1] <= 90;
}

function isValidRing(ring) {
  if (!Array.isArray(ring) || ring.length < 4 || !ring.every(isValidPosition)) {
    return false;
  }
  const first = ring[0];
  const last = ring[ring.length - 1];
  return first[0] === last[0] && first[1] === last[1];
}

function isRenderablePolygonFeature(feature) {
  const geometry = feature?.geometry;
  if (feature?.type !== "Feature" || !geometry) return false;

  if (geometry.type === "Polygon") {
    return Array.isArray(geometry.coordinates)
      && geometry.coordinates.length > 0
      && geometry.coordinates.every(isValidRing);
  }

  if (geometry.type === "MultiPolygon") {
    return Array.isArray(geometry.coordinates)
      && geometry.coordinates.length > 0
      && geometry.coordinates.every((polygon) =>
        Array.isArray(polygon)
        && polygon.length > 0
        && polygon.every(isValidRing)
      );
  }

  return false;
}

function parseBuildingHeight(value) {
  if (typeof value === "number") {
    return Number.isFinite(value) && value > 0 ? value : null;
  }
  if (typeof value !== "string") return null;
  const match = value.match(/^\s*(\d+(?:\.\d+)?)\s*(?:m|meters?|metres?)?\s*$/i);
  if (!match) return null;
  const height = Number(match[1]);
  return Number.isFinite(height) && height > 0 ? height : null;
}

export default function CesiumViewer() {

  const containerRef = useRef(null);
  const { state } = useLocation();
  const analysis = useMemo(() => state?.analysis ?? readSavedAnalysis(), [state?.analysis]);
  const geojson = analysis?.buildings?.geojson;
  const renderableGeojson = useMemo(() => {
    if (geojson?.type !== "FeatureCollection" || !Array.isArray(geojson.features)) {
      return null;
    }
    return {
      type: "FeatureCollection",
      features: geojson.features.filter(isRenderablePolygonFeature),
    };
  }, [geojson]);
  const [loadState, setLoadState] = useState(null);
  const loading = loadState?.geojson !== renderableGeojson;
  const loadError = loading ? "" : loadState?.error ?? "";

  useEffect(() => {
    if (!renderableGeojson || renderableGeojson.features.length === 0 || !containerRef.current) {
      return;

    }

    let cancelled = false;
    let viewer;

    async function loadBuildings() {
      try {
        await Promise.resolve();
        if (cancelled) return;

        viewer = new Viewer(containerRef.current, {
  animation: false,
  timeline: false,
  baseLayerPicker: false,
  geocoder: false,
  homeButton: false,
  sceneModePicker: false,
  navigationHelpButton: false,
  baseLayer: false,
  globe: false,
  skyBox: false,
  skyAtmosphere: false,
  scene3DOnly: true,
});
const positions = renderableGeojson.features.flatMap((feature) => {
  const points = [];

  function collect(coords) {
    if (!Array.isArray(coords)) return;

    if (typeof coords[0] === "number") {
      points.push(coords);
      return;
    }

    coords.forEach(collect);
  }

  collect(feature.geometry.coordinates);
  return points;
});

if (positions.length > 0) {
  const longitudes = positions.map((p) => p[0]);
  const latitudes = positions.map((p) => p[1]);

  viewer.entities.add({
    name: "Flat Ground",
    rectangle: {
      coordinates: Rectangle.fromDegrees(
        Math.min(...longitudes),
        Math.min(...latitudes),
        Math.max(...longitudes),
        Math.max(...latitudes)
      ),
      height: 0,
      material: Color.DARKGRAY,
      outline: false,

    },
  });
}

        const dataSource = await GeoJsonDataSource.load(renderableGeojson, {
          clampToGround: false,
          stroke: Color.DARKSLATEGRAY,
          fill: Color.DODGERBLUE.withAlpha(0.75),
          strokeWidth: 2,
        });

        if (cancelled || viewer.isDestroyed()) return;

        if (dataSource.entities.values.length === 0) {
          setLoadState({
            geojson: renderableGeojson,
            error: "No building footprints could be displayed for this area.",
          });
          return;
        }

        await viewer.dataSources.add(dataSource);
        if (cancelled || viewer.isDestroyed()) return;

        for (const entity of dataSource.entities.values) {
          if (!entity.polygon) continue;

          const heightProperty = entity.properties?.height;
          const heightValue = heightProperty?.getValue();
          const height = parseBuildingHeight(heightValue);
          entity.polygon.heightReference = HeightReference.CLAMP_TO_GROUND;
          entity.polygon.extrudedHeightReference = HeightReference.RELATIVE_TO_GROUND;
          entity.polygon.extrudedHeight = height ?? DEFAULT_DISPLAY_HEIGHT_M;
        }

        await viewer.zoomTo(dataSource);

if (cancelled || viewer.isDestroyed()) return;

// Mark Cesium loading as complete
setLoadState({
  geojson: renderableGeojson,
  error: "",
});

// Focus closely on the generated buildings.
viewer.scene.screenSpaceCameraController.minimumZoomDistance = 20;

viewer.camera.lookAtTransform(Matrix4.IDENTITY);
      } catch (error) {
        if (cancelled) return;
        console.error("Could not display building GeoJSON in Cesium.", error);
        setLoadState({
          geojson: renderableGeojson,
          error: "Could not display the building footprints. Please return to the map and try again.",
        });
      }
    }

    loadBuildings();

    return () => {
      cancelled = true;
      if (viewer && !viewer.isDestroyed()) {
        viewer.destroy();
      }
    };
  }, [renderableGeojson]);

  if (!renderableGeojson || renderableGeojson.features.length === 0) {
    return (
      <main className="solar-page empty-view">
        <div className="empty-card">
          <p className="eyebrow">3D BUILDINGS</p>
          <h1>{geojson?.features?.length ? "No valid footprints to display" : "No footprints to display"}</h1>
          <p className="muted">
            {geojson?.features?.length
              ? "The returned building data did not contain valid Polygon or MultiPolygon geometry."
              : "Return to the map, draw an area, and load its building footprints to view them in Cesium."}
          </p>
          <Link className="button button-primary" to="/map">Back to area selection</Link>
        </div>
      </main>
    );
  }

  return (
    <main style={{ width: "100%", height: "100vh", position: "relative" }}>
      <div ref={containerRef} style={{ width: "100%", height: "100vh" }} />
      <nav aria-label="Cesium map actions" aria-busy={loading} style={{ position: "absolute", top: 16, left: 16, zIndex: 1, display: "flex", gap: 12, alignItems: "center", padding: 12, borderRadius: 8, background: "white" }}>
        <Link className="button button-secondary" to="/map">Back to area selection</Link>
        {loading
          ? <span aria-live="polite"><span className="spinner spinner-dark" /> Loading building footprints…</span>
          : loadError
            ? <span role="alert" style={{ color: "#983a2f" }}>{loadError}</span>
            : <span aria-live="polite">{renderableGeojson.features.length} building footprint{renderableGeojson.features.length === 1 ? "" : "s"} loaded. Missing heights use a {DEFAULT_DISPLAY_HEIGHT_M} m display height.</span>}
      </nav>
    </main>
  );
}
