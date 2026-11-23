"use strict";

const siteHeader = document.querySelector(".top");

function updateHeader() {
  const threshold = siteHeader.classList.contains("is-compact") ? 48 : 112;
  siteHeader.classList.toggle("is-compact", window.scrollY > threshold);
}

window.addEventListener("scroll", updateHeader, { passive: true });
updateHeader();

const data = window.PILOT_DATA;
const map = document.querySelector("#map");
const canvas = document.querySelector("#map-overlay");
const context = canvas.getContext("2d");
const markerLayer = document.querySelector("#markers");
const settlementSelect = document.querySelector("#settlement");
const networkSelect = document.querySelector("#network");
const markerById = new Map();
let selected = data.settlements[0].id;
let preferredNetwork = networkSelect.value;
let activeCase;
let activeView;
let selectedSites;
document.querySelector("#terrain-credit").textContent = data.terrainCredit;

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
  const label = document.createElement("span");
  label.className = "marker-label";
  label.textContent = settlement.name;
  marker.append(label);
  marker.addEventListener("click", () => {
    selected = settlement.id;
    render();
  });
  markerLayer.append(marker);
  markerById.set(settlement.id, marker);
}

function drawMap() {
  const width = map.clientWidth;
  const height = map.clientHeight;
  const pixelRatio = window.devicePixelRatio || 1;
  canvas.width = width * pixelRatio;
  canvas.height = height * pixelRatio;
  context.scale(pixelRatio, pixelRatio);
  context.beginPath();
  for (const [index, [x, y]] of data.boundary.entries()) {
    if (index === 0) context.moveTo(x * width, y * height);
    else context.lineTo(x * width, y * height);
  }
  context.closePath();
  context.setLineDash([6, 5]);
  context.lineWidth = 1.5;
  context.strokeStyle = "rgba(255,255,255,.9)";
  context.stroke();
  context.setLineDash([]);

  const sites = data.sites[activeCase.spacing];
  const displayIds = selectedSites ?? Object.keys(sites);
  const size = selectedSites ? 7 : 4.25;
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
    context.lineWidth = selectedSites ? 4 : 2.6;
    context.stroke();
    context.strokeStyle = siteColor;
    context.lineWidth = selectedSites ? 2.2 : 1.2;
    context.stroke();
  }

  const detail = activeView.settlements[selected];
  if (detail.bestSite) {
    const [x, y] = sites[detail.bestSite];
    const settlement = data.settlements.find(item => item.id === selected);
    context.beginPath();
    context.moveTo(x * width, y * height);
    context.lineTo(settlement.x * width, settlement.y * height);
    context.strokeStyle = "#fff";
    context.lineWidth = 4;
    context.stroke();
    context.strokeStyle = "#124638";
    context.lineWidth = 2;
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
  document.querySelector("#site-label").textContent = selectedSites ? "selected sites" : "candidate sites";
  document.querySelector("#legend-mast").classList.toggle("candidate", !selectedSites);
  document.querySelector("#legend-site").textContent = selectedSites ? "Selected site" : "Candidate site";
  document.querySelector("#links").textContent = activeView.links;

  for (const settlement of data.settlements) {
    const marker = markerById.get(settlement.id);
    const reachable = activeView.settlements[settlement.id].count > 0;
    marker.className = "marker " + (reachable ? "reached" : "unreached");
    marker.setAttribute("aria-label", settlement.name + (reachable ? ", reachable" : ", no passing link"));
    marker.setAttribute("aria-pressed", String(settlement.id === selected));
  }
  settlementSelect.value = selected;
  const settlement = data.settlements.find(item => item.id === selected);
  const detail = activeView.settlements[selected];
  document.querySelector("#settlement-name").textContent = settlement.name;
  const reason = terrainEnabled && activeCase.variants.fspl_only.settlements[selected].count > 0
    ? "Terrain blocks the paths that pass the signal-strength check."
    : "None of the candidates meets the signal-strength threshold.";
  const siteType = selectedSites ? "selected" : "candidate";
  document.querySelector("#settlement-detail").textContent = detail.count
    ? detail.count + " " + siteType + (detail.count === 1 ? " site has" : " sites have") +
      " a usable link. The map draws the strongest passing link."
    : "No displayed site has a usable link. " + reason;
  drawMap();
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
new ResizeObserver(drawMap).observe(map);
render();
