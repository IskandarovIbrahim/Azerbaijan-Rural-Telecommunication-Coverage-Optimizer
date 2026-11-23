"use strict";

const siteHeader = document.querySelector(".top");

function updateHeader() {
  const threshold = siteHeader.classList.contains("is-compact") ? 48 : 112;
  siteHeader.classList.toggle("is-compact", window.scrollY > threshold);
}

window.addEventListener("scroll", updateHeader, { passive: true });
updateHeader();

const areas = window.PILOT_DATA.areas;
const areaSelect = document.querySelector("#study-area");
const map = document.querySelector("#map");
const canvas = document.querySelector("#map-overlay");
const context = canvas.getContext("2d");
const markerLayer = document.querySelector("#markers");
const settlementSelect = document.querySelector("#settlement");
const networkSelect = document.querySelector("#network");
const markerById = new Map();
let data;
let selected;
let preferredNetwork = networkSelect.value;
let activeCase;
let activeView;
let selectedSites;
const mapCamera = createMapCamera(map, document.querySelector("#map-layer"), drawMap);
const terrainDetails = createTerrainDetails(map, render);
function createSettlementControls() {
  const labeled = new Set(data.mapLabels.map(place => place.id));
  for (const settlement of data.settlements) {
    const option = document.createElement("option");
    option.value = settlement.id;
    option.textContent = settlement.name;
    settlementSelect.append(option);

    const marker = document.createElement("button");
    marker.type = "button";
    marker.className = "marker";
    marker.style.left = (settlement.x * 100) + "%";
    marker.style.top = (settlement.y * 100) + "%";
    if (!labeled.has(settlement.id)) {
      const label = document.createElement("span");
      label.className = "marker-label";
      label.textContent = settlement.name;
      marker.append(label);
    }
    marker.addEventListener("click", () => {
      selected = settlement.id;
      render();
    });
    markerLayer.append(marker);
    markerById.set(settlement.id, marker);
  }
}

function drawMap() {
  const width = map.clientWidth;
  const height = map.clientHeight;
  const scale = mapCamera.scale;
  const pixelRatio = Math.min((window.devicePixelRatio || 1) * scale, 4);
  canvas.width = width * pixelRatio;
  canvas.height = height * pixelRatio;
  context.scale(pixelRatio, pixelRatio);
  context.beginPath();
  for (const [index, [x, y]] of data.boundary.entries()) {
    if (index === 0) context.moveTo(x * width, y * height);
    else context.lineTo(x * width, y * height);
  }
  context.closePath();
  context.setLineDash([6 / scale, 5 / scale]);
  context.lineWidth = 1.5 / scale;
  context.strokeStyle = "rgba(255,255,255,.9)";
  context.stroke();
  context.setLineDash([]);

  const sites = data.sites[activeCase.spacing];
  const displayIds = selectedSites ?? Object.keys(sites);
  const size = (selectedSites ? 7 : 4.25) / scale;
  const siteColor = selectedSites ? "#975a1a" : "#365f55";
  context.lineCap = "round";
  context.lineJoin = "round";
  for (const id of displayIds) {
    const [x, y] = sites[id];
    const cx = x * width;
    const cy = y * height;
    context.beginPath();
    context.moveTo(cx - size * .62, cy + size);
    context.lineTo(cx, cy - size);
    context.lineTo(cx + size * .62, cy + size);
    context.moveTo(cx - size * .31, cy - size * .4);
    context.lineTo(cx + size * .31, cy - size * .4);
    context.moveTo(cx - size * .36, cy + size * .4);
    context.lineTo(cx + size * .36, cy + size * .4);
    context.strokeStyle = "#fff";
    context.lineWidth = (selectedSites ? 4 : 2.6) / scale;
    context.stroke();
    context.strokeStyle = siteColor;
    context.lineWidth = (selectedSites ? 2.2 : 1.2) / scale;
    context.stroke();
  }

  const detail = activeView.settlements[selected];
  const blocked = terrainDetails.showElevation ? detail.obstruction : undefined;
  const linkSite = detail.bestSite ?? blocked?.site;
  if (linkSite) {
    const [x, y] = sites[linkSite];
    const settlement = data.settlements.find(item => item.id === selected);
    context.beginPath();
    context.moveTo(x * width, y * height);
    context.lineTo(settlement.x * width, settlement.y * height);
    context.strokeStyle = "#fff";
    context.lineWidth = 4 / scale;
    context.stroke();
    context.strokeStyle = blocked ? "#983c2d" : "#124638";
    if (blocked) context.setLineDash([5 / scale, 4 / scale]);
    context.lineWidth = 2 / scale;
    context.stroke();
  }
}

function render() {
  const height = document.querySelector('input[name="height"]:checked').value;
  const spacing = document.querySelector('input[name="spacing"]:checked').value;
  const mode = document.querySelector('input[name="model"]:checked').value;
  const terrainEnabled = mode === "terrain_los";
  activeCase = data.cases[height + "-" + spacing];
  networkSelect.disabled = !terrainEnabled;
  networkSelect.value = terrainEnabled ? preferredNetwork : "all";
  activeView = networkSelect.value === "all"
    ? activeCase.variants[mode]
    : activeCase.selections[networkSelect.value];
  selectedSites = activeView.siteIds;
  document.querySelector("#network-hint").textContent = terrainEnabled
    ? "Both selections use terrain-aware links."
    : "Turn terrain back on to inspect selected towers.";
  document.querySelector("#reachable").textContent = activeView.reachable;
  document.querySelector("#site-count").textContent = selectedSites?.length ?? activeCase.candidates;
  document.querySelector("#site-label").textContent = selectedSites ? "proposed towers" : "candidate sites";
  document.querySelector("#legend-mast").classList.toggle("candidate", !selectedSites);
  document.querySelector("#legend-site").textContent = selectedSites ? "Proposed tower" : "Candidate site";
  document.querySelector("#links").textContent = activeView.links;

  for (const settlement of data.settlements) {
    const marker = markerById.get(settlement.id);
    const reachable = activeView.settlements[settlement.id].count > 0;
    marker.className = "marker " + (reachable ? "reached" : "unreached");
    marker.setAttribute("aria-label", settlement.name + (reachable ? ", reachable" : ", no passing link"));
    marker.setAttribute("aria-pressed", String(settlement.id === selected));
  }
  terrainDetails.highlightPlace(selected);
  settlementSelect.value = selected;
  const settlement = data.settlements.find(item => item.id === selected);
  const detail = activeView.settlements[selected];
  document.querySelector("#settlement-name").textContent = settlement.name;
  const reason = terrainEnabled && activeCase.variants.fspl_only.settlements[selected].count > 0
    ? "Terrain blocks the paths that pass the signal-strength check."
    : "None of the candidates meets the signal-strength threshold.";
  const siteType = selectedSites ? "proposed tower" : "candidate site";
  document.querySelector("#settlement-detail").textContent = detail.count
    ? detail.count + " " + siteType + (detail.count === 1 ? " has" : "s have") +
      " a usable link. The map draws the strongest passing link."
    : "No displayed site has a usable link. " + reason +
      (terrainDetails.showElevation && detail.obstruction
        ? " The dashed path is obstructed by up to " + Math.round(-detail.obstruction.clearance) + " m of terrain."
        : "");
  drawMap();
}

function renderResults() {
  const results = Object.values(data.cases);
  const total = data.settlements.length;
  const terrainCount = item => item.variants.terrain_los.reachable;
  const best = results.reduce((winner, item) => terrainCount(item) > terrainCount(winner) ? item : winner);
  const bestCount = terrainCount(best);
  document.querySelector("#best-reach").textContent = bestCount + " of " + total;
  document.querySelector("#best-description").textContent =
    "Settlements reachable with " + best.selections.exact.siteIds.length + " " + best.height +
    " m towers chosen from the " + best.spacing + " km grid.";
  const ties = results.filter(item => item.selections.greedy.siteIds.length === item.selections.exact.siteIds.length).length;
  document.querySelector("#method-agreement").textContent =
    "Greedy matched the minimum tower count in " + ties + " of " + results.length + " scenarios.";
  document.querySelector("#result-context").textContent = (total - bestCount) +
    " of " + total + " settlements lack a passing link in the highest-reach scenario.";
  document.querySelector("#result-rows").replaceChildren(...results.map(item => {
    const row = document.createElement("tr");
    const mast = document.createElement("th");
    mast.scope = "row";
    mast.textContent = item.height + " m";
    row.append(mast);
    for (const value of [item.spacing + " km", item.candidates, terrainCount(item) + " of " + total,
                         item.selections.exact.siteIds.length]) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    }
    return row;
  }));
}

function renderArea() {
  data = areas[areaSelect.value];
  selected = data.settlements[0].id;
  terrainDetails.setArea(data);
  document.querySelector("#settlement-total").textContent = data.settlements.length;
  document.querySelector("#area-result-name").textContent = data.label;
  document.querySelector("#area-cost-name").textContent = data.label;
  document.querySelector("#terrain-credit").textContent = data.terrainCredit;
  markerLayer.replaceChildren();
  settlementSelect.replaceChildren();
  markerById.clear();
  createSettlementControls();
  render();
  renderResults();
  mapCamera.reset();
}

document.querySelectorAll(".choices input").forEach(input => input.addEventListener("change", render));
networkSelect.addEventListener("change", () => {
  preferredNetwork = networkSelect.value;
  render();
});
settlementSelect.addEventListener("change", () => {
  selected = settlementSelect.value;
  render();
});
areaSelect.addEventListener("change", renderArea);
renderArea();
new ResizeObserver(() => {
  mapCamera.resize();
  drawMap();
}).observe(map);
