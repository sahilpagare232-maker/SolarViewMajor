
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import {
  Viewer,
  GeoJsonDataSource,
  Color,
  HeightReference,
  Matrix4,
  Rectangle,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType
} from "cesium";

import "cesium/Build/Cesium/Widgets/widgets.css";
import { optimizeBuilding as requestBuildingOptimization } from "../services/solarService";

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
  const viewerRef = useRef(null);
  const panelDataSourceRef = useRef(null);
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
  const [selectedBuilding, setSelectedBuilding] = useState(null);
  const [panelResult, setPanelResult] = useState(null);
  const [panelLoading, setPanelLoading] = useState(false);
  const [panelError, setPanelError] = useState("");
  const loading = loadState?.geojson !== renderableGeojson;
  const loadError = loading ? "" : loadState?.error ?? "";

  useEffect(() => {
    if (!renderableGeojson || renderableGeojson.features.length === 0 || !containerRef.current) {
      return;

    }

    let cancelled = false;
    let viewer;
    let selectionHandler;

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
  infoBox: false,
  selectionIndicator: false,
});
viewerRef.current = viewer;
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

        selectionHandler = new ScreenSpaceEventHandler(viewer.scene.canvas);
        selectionHandler.setInputAction((movement) => {
          const pickedEntity = viewer.scene.pick(movement.position)?.id;
          if (!pickedEntity || !dataSource.entities.contains(pickedEntity)) {
            setSelectedBuilding(null);
            setPanelResult(null);
            setPanelError("");
            if (panelDataSourceRef.current) {
              viewer.dataSources.remove(panelDataSourceRef.current, true);
              panelDataSourceRef.current = null;
            }
            return;
          }

          const properties = pickedEntity.properties?.getValue(viewer.clock.currentTime) ?? {};
          const buildingId = String(properties.building_id ?? pickedEntity.id ?? "");
          const feature = renderableGeojson.features.find((item) =>
            String(item.properties?.building_id ?? item.id ?? "") === buildingId
          );
          if (!feature) return;

          if (panelDataSourceRef.current) {
            viewer.dataSources.remove(panelDataSourceRef.current, true);
            panelDataSourceRef.current = null;
          }
          setPanelResult(null);
          setPanelError("");
          setSelectedBuilding({
            building_id: buildingId,
            geometry: feature.geometry,
            height_m: parseBuildingHeight(feature.properties?.height),
            building_type: feature.properties?.building_type || "Building",
          });
        }, ScreenSpaceEventType.LEFT_CLICK);

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
      selectionHandler?.destroy();
      viewerRef.current = null;
      panelDataSourceRef.current = null;
      if (viewer && !viewer.isDestroyed()) {
        viewer.destroy();
      }
    };
  }, [renderableGeojson]);

  async function handleOptimizeSelectedBuilding() {
    if (!selectedBuilding || !analysis?.area || panelLoading) return;
    setPanelLoading(true);
    setPanelError("");
    setPanelResult(null);
    try {
      const result = await requestBuildingOptimization({
        building_id: selectedBuilding.building_id,
        geometry: selectedBuilding.geometry,
        coordinates: analysis.area,
        height_m: selectedBuilding.height_m,
      });
      const viewer = viewerRef.current;
      if (!viewer || viewer.isDestroyed()) return;

      const dataSource = await GeoJsonDataSource.load(result.panel_layout, {
        clampToGround: false,
        stroke: Color.DARKGOLDENROD,
        fill: Color.GOLD.withAlpha(0.95),
        strokeWidth: 1,
      });
      if (viewer.isDestroyed()) return;
      const displayRoofHeight = selectedBuilding.height_m ?? DEFAULT_DISPLAY_HEIGHT_M;
      for (const entity of dataSource.entities.values) {
        if (!entity.polygon) continue;
        entity.polygon.height = displayRoofHeight + 0.08;
        entity.polygon.extrudedHeight = displayRoofHeight + 0.18;
        entity.polygon.heightReference = HeightReference.RELATIVE_TO_GROUND;
        entity.polygon.extrudedHeightReference = HeightReference.RELATIVE_TO_GROUND;
        entity.polygon.material = Color.GOLD.withAlpha(0.98);
        entity.polygon.outline = true;
        entity.polygon.outlineColor = Color.DARKGOLDENROD;
      }
      await viewer.dataSources.add(dataSource);
      panelDataSourceRef.current = dataSource;
      setPanelResult(result);
    } catch (error) {
      setPanelError(error.message || "Panel placement failed. Select another building and try again.");
    } finally {
      setPanelLoading(false);
    }
  }

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
      <nav aria-label="Cesium map actions" aria-busy={loading} style={{ position: "absolute", top: 16, left: 16, zIndex: 1, display: "flex", gap: 12, alignItems: "center", padding: 12, borderRadius: 8, background: "white", boxShadow: "0 2px 12px #0002" }}>
        <Link className="button button-secondary" to="/map">Back to area selection</Link>
        {loading
          ? <span aria-live="polite"><span className="spinner spinner-dark" /> Loading building footprints…</span>
          : loadError
            ? <span role="alert" style={{ color: "#983a2f" }}>{loadError}</span>
            : <span aria-live="polite">{renderableGeojson.features.length} building footprint{renderableGeojson.features.length === 1 ? "" : "s"} loaded. Click a building to place panels.</span>}
      </nav>
      {selectedBuilding && !loading && !loadError && <section aria-label="Selected building panel placement" style={{ position: "absolute", top: 86, left: 16, zIndex: 1, width: "min(360px, calc(100vw - 32px))", padding: 18, border: "1px solid #e5eae4", borderRadius: 12, background: "white", boxShadow: "0 4px 18px #0002", color: "#182820" }}>
        <p className="eyebrow" style={{ marginBottom: 6 }}>SELECTED ROOFTOP</p>
        <h2 style={{ margin: "0 0 6px", fontSize: 17 }}>{selectedBuilding.building_type}</h2>
        <p style={{ margin: "0 0 14px", color: "#77847c", fontSize: 12 }}>OSM ID {selectedBuilding.building_id} · {selectedBuilding.height_m == null ? "Height unavailable" : `${selectedBuilding.height_m} m tagged height`}</p>
        <button className="button button-primary" type="button" onClick={handleOptimizeSelectedBuilding} disabled={panelLoading} style={{ width: "100%" }}>
          {panelLoading ? <><span className="spinner" /> Placing panels…</> : "Optimize panel placement"}
        </button>
        {panelError && <p role="alert" style={{ margin: "12px 0 0", color: "#983a2f", fontSize: 12 }}>{panelError}</p>}
        {panelResult && <div aria-live="polite" style={{ marginTop: 14, borderTop: "1px solid #e5eae4", paddingTop: 12, fontSize: 12, lineHeight: 1.7 }}>
          <strong>{panelResult.panel_count} panels</strong> · {panelResult.installed_capacity_kw} kWp<br />
          Grid orientation {panelResult.placement_orientation_deg ?? "—"}°<br />
          Usable roof {panelResult.usable_area_m2} m² · Coverage {panelResult.panel_coverage_percent}%<br />
          Annual energy ≈ {Number(panelResult.annual_energy_kwh).toLocaleString()} kWh
          <p style={{ margin: "8px 0 0", color: "#77847c", fontSize: 10 }}>{panelResult.roof_assumption}. Energy is {panelResult.annual_energy_data_class}. {selectedBuilding.height_m == null ? `For display only, panels use the existing ${DEFAULT_DISPLAY_HEIGHT_M} m placeholder building height.` : "Roof height uses the OSM height tag."}</p>
        </div>}
      </section>}
    </main>
  );
}
