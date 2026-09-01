import { Streamlit } from "streamlit-component-lib";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet-draw";
import "leaflet-draw/dist/leaflet.draw.css";
import "./source.css";

let map = null;
let editable = null;
let drawControl = null;

function setStatus(message, tone = "normal") {
  const box = document.getElementById("status");
  box.textContent = message;
  box.dataset.tone = tone;
}

const OfflineGrid = L.GridLayer.extend({
  createTile(coords) {
    const tile = document.createElement("canvas");
    tile.width = 256;
    tile.height = 256;
    const ctx = tile.getContext("2d");
    ctx.fillStyle = "#eef2f3";
    ctx.fillRect(0, 0, 256, 256);
    ctx.strokeStyle = "#cbd5e1";
    ctx.lineWidth = 1;
    for (let value = 0; value <= 256; value += 32) {
      ctx.beginPath(); ctx.moveTo(value, 0); ctx.lineTo(value, 256); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, value); ctx.lineTo(256, value); ctx.stroke();
    }
    ctx.fillStyle = "#64748b";
    ctx.font = "600 12px system-ui, sans-serif";
    ctx.fillText(`offline grid · z${coords.z}`, 12, 24);
    return tile;
  }
});

function geometryOnly(feature) {
  if (!feature) return null;
  if (feature.type === "Feature") return feature.geometry;
  if (feature.type === "FeatureCollection") {
    const polygons = (feature.features || []).map(item => item.geometry).filter(Boolean);
    if (polygons.length === 1) return polygons[0];
    return { type: "GeometryCollection", geometries: polygons };
  }
  return feature;
}

function emitGeometry(action = "updated") {
  const layers = editable.getLayers();
  if (!layers.length) {
    Streamlit.setComponentValue({ geometry: null, action: "deleted" });
    setStatus("No editable boundary. Draw a polygon or rectangle.", "warning");
    return;
  }
  const collection = editable.toGeoJSON();
  let geometry = null;
  if (collection.features.length === 1) {
    geometry = collection.features[0].geometry;
  } else {
    geometry = {
      type: "MultiPolygon",
      coordinates: collection.features
        .map(item => item.geometry)
        .filter(item => item && item.type === "Polygon")
        .map(item => item.coordinates),
    };
  }
  Streamlit.setComponentValue({ geometry, action });
  setStatus("Boundary captured locally. Save it in the form below.", "success");
}

function addEditableGeometry(geometry) {
  if (!geometry) return;
  try {
    const layer = L.geoJSON(geometry, {
      style: { color: "#dc2626", weight: 4, fillColor: "#fb7185", fillOpacity: 0.18 }
    });
    layer.eachLayer(child => editable.addLayer(child));
  } catch (error) {
    setStatus(`Saved boundary could not be loaded: ${error.message}`, "warning");
  }
}

function addReferenceGeometry(item, index, bounds) {
  if (!item || !item.geometry) return;
  const colour = item.color || "#059669";
  const layer = L.geoJSON(item.geometry, {
    style: {
      color: colour, weight: Number(item.weight || 4),
      dashArray: item.dash || "9 6", fillColor: colour,
      fillOpacity: Number(item.fill_opacity ?? 0.04)
    }
  }).bindTooltip(item.label || `Reference boundary ${index + 1}`);
  layer.addTo(map);
  if (layer.getBounds && layer.getBounds().isValid()) bounds.push(layer.getBounds());
}

function render(event) {
  const args = event.detail.args || {};
  const height = Math.max(360, Number(args.height || 520));
  document.documentElement.style.setProperty("--map-height", `${height}px`);
  Streamlit.setFrameHeight(height + 8);

  if (map) {
    map.off();
    map.remove();
    map = null;
  }
  document.getElementById("map").innerHTML = "";
  const center = Array.isArray(args.center) && args.center.length === 2 ? args.center : [19.45, -98.90];
  map = L.map("map", { center, zoom: Number(args.zoom || 15), zoomControl: true, preferCanvas: true });
  const offline = new OfflineGrid({ minZoom: 2, maxZoom: 22, attribution: "AGROLATTICE offline grid" });
  const roads = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 20, attribution: "© OpenStreetMap contributors", crossOrigin: true
  });
  const satellite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
    maxZoom: 20, attribution: "Esri, Maxar, Earthstar Geographics", crossOrigin: true
  });
  const bases = { "Satellite imagery": satellite, "Roads & places": roads, "Offline grid": offline };
  let active = args.satellite_default === false ? roads : satellite;
  active.addTo(map);
  L.control.layers(bases, {}, { position: "topright", collapsed: false }).addTo(map);
  L.control.scale({ metric: true, imperial: false }).addTo(map);

  let tileErrors = 0;
  function handleTileError() {
    tileErrors += 1;
    if (tileErrors >= 4 && !map.hasLayer(offline)) {
      map.removeLayer(active);
      active = offline;
      offline.addTo(map);
      setStatus("Online tiles are unavailable; the local editor switched to its offline grid.", "warning");
    }
  }
  roads.on("tileerror", handleTileError);
  satellite.on("tileerror", handleTileError);

  editable = new L.FeatureGroup();
  editable.addTo(map);
  addEditableGeometry(geometryOnly(args.initial_geometry));
  const allBounds = [];
  if (editable.getLayers().length) {
    const editableBounds = editable.getBounds();
    if (editableBounds.isValid()) allBounds.push(editableBounds);
  }
  (args.reference_geometries || []).forEach((item, index) => addReferenceGeometry(item, index, allBounds));

  if (args.drawing_enabled !== false) {
    drawControl = new L.Control.Draw({
      position: "topleft",
      draw: {
        polygon: { allowIntersection: false, showArea: true, metric: true, shapeOptions: { color: "#dc2626", weight: 4 } },
        rectangle: { showArea: true, metric: true, shapeOptions: { color: "#dc2626", weight: 4 } },
        polyline: false, circle: false, circlemarker: false, marker: false
      },
      edit: { featureGroup: editable, edit: true, remove: true }
    });
    map.addControl(drawControl);
    map.on(L.Draw.Event.CREATED, drawEvent => {
      editable.clearLayers();
      editable.addLayer(drawEvent.layer);
      emitGeometry("created");
    });
    map.on(L.Draw.Event.EDITED, () => emitGeometry("edited"));
    map.on(L.Draw.Event.DELETED, () => emitGeometry("deleted"));
  }

  if (allBounds.length) {
    const combined = allBounds.reduce((result, item) => result.extend(item), L.latLngBounds([]));
    if (combined.isValid()) map.fitBounds(combined, { padding: [28, 28], maxZoom: 19 });
  }
  setTimeout(() => map.invalidateSize(), 50);
  setStatus(editable.getLayers().length ? "Saved boundary loaded. Use edit or delete to change it." : "Draw a polygon or rectangle. The editor is loaded from this installation.");
}

Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, render);
Streamlit.setComponentReady();
Streamlit.setFrameHeight(528);
