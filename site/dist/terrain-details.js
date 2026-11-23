"use strict";

function createTerrainDetails(map, onViewChange) {
  const toggle = document.querySelector("#show-elevation");
  const legend = document.querySelector("#elevation-key");
  const colorBar = legend.querySelector(".elevation-ramp");
  const units = legend.querySelector(".elevation-units");
  const reading = document.querySelector("#elevation-reading");
  const labels = map.querySelector(".map-place-labels");
  const pin = map.querySelector(".elevation-pin");
  const layer = map.querySelector("#map-layer");
  const image = layer.querySelector("img");
  const cache = new WeakMap();
  let area;
  let request = 0;

  function refreshView() {
    request++;
    pin.hidden = true;
    image.src = toggle.checked ? area.elevation.image : area.terrainImage;
    image.alt = (toggle.checked ? "Elevation map for " : "Shaded terrain for ") + area.label;
    legend.hidden = !toggle.checked;
    reading.hidden = !toggle.checked;
    reading.textContent = "Click the terrain to read the height of its 90 m cell.";
  }

  function setArea(next) {
    area = next;
    labels.replaceChildren(...area.mapLabels.map(place => {
      const label = document.createElement("span");
      label.textContent = place.name;
      label.style.left = (place.x * 100) + "%";
      label.style.top = (place.y * 100) + "%";
      return label;
    }));
    const stops = area.elevation.legend;
    const top = stops.at(-1)[0];
    colorBar.style.background = "linear-gradient(90deg, " + stops.map(([meters, rgb]) =>
      "rgb(" + rgb.join(",") + ") " + (meters / top * 100) + "%"
    ).join(",") + ")";
    units.replaceChildren(...stops.map(([meters]) => {
      const tick = document.createElement("span");
      tick.textContent = meters.toLocaleString("en") + " m";
      tick.style.left = (meters / top * 100) + "%";
      return tick;
    }));
    refreshView();
  }

  function heightSamples(elevation) {
    if (!cache.has(elevation)) {
      const bytes = Uint8Array.from(atob(elevation.samples), character => character.charCodeAt(0));
      const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
      cache.set(elevation, new Response(stream).arrayBuffer().then(buffer => new DataView(buffer)));
    }
    return cache.get(elevation);
  }

  map.addEventListener("click", async event => {
    if (!toggle.checked || event.target.closest(".map-tools, .marker")) return;
    const frame = layer.getBoundingClientRect();
    const x = (event.clientX - frame.left) / frame.width;
    const y = (event.clientY - frame.top) / frame.height;
    if (x < 0 || x >= 1 || y < 0 || y >= 1) return;
    const point = ++request;
    const elevation = area.elevation;
    const col = Math.floor(x * elevation.width);
    const row = Math.floor(y * elevation.height);
    try {
      const samples = await heightSamples(elevation);
      if (point !== request) return;
      const meters = samples.getInt16((row * elevation.width + col) * 2, true);
      if (meters === -32768) {
        pin.hidden = true;
        reading.textContent = "Elevation is unavailable for this cell.";
        return;
      }
      pin.style.left = ((col + .5) / elevation.width * 100) + "%";
      pin.style.top = ((row + .5) / elevation.height * 100) + "%";
      pin.hidden = false;
      reading.textContent = meters.toLocaleString("en") + " m above sea level · 90 m cell";
    } catch {
      if (point === request) reading.textContent = "The height sample could not be read in this browser.";
    }
  });

  toggle.addEventListener("change", () => {
    refreshView();
    onViewChange();
  });
  return {setArea, get showElevation() { return toggle.checked; }};
}
