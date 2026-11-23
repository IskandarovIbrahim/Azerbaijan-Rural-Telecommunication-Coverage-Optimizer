"use strict";

const data = window.PILOT_DATA;
const map = document.querySelector("#map");
const canvas = document.querySelector("#map-overlay");
const context = canvas.getContext("2d");
const markerLayer = document.querySelector("#markers");
const settlementSelect = document.querySelector("#settlement");
const sitesToggle = document.querySelector("#show-sites");
const markerById = new Map();
let selected = data.settlements[0].id;
let activeCase;
let variant;
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
  marker.addEventListener("click", () => { selected = settlement.id; render(); });
  markerLayer.append(marker);
  markerById.set(settlement.id, marker);
}

function drawMap() {
  if (!activeCase) return;
  const width = map.clientWidth;
  const height = map.clientHeight;
  const pixelRatio = window.devicePixelRatio || 1;
  canvas.width = width * pixelRatio;
  canvas.height = height * pixelRatio;
  context.scale(pixelRatio, pixelRatio);
  const boundary = data.boundary;
  context.beginPath();
  boundary.forEach(([x, y], index) => index ? context.lineTo(x * width, y * height) : context.moveTo(x * width, y * height));
  context.closePath();
  context.setLineDash([6, 5]);
  context.lineWidth = 1.5;
  context.strokeStyle = "rgba(255,255,255,.86)";
  context.stroke();
  context.setLineDash([]);
  const sites = data.sites[activeCase.spacing];
  if (sitesToggle.checked) {
    context.fillStyle = "#385a78";
    context.strokeStyle = "#f3f7f0";
    context.lineWidth = 1;
    for (const [x, y] of Object.values(sites)) {
      context.beginPath();
      context.moveTo(x * width, y * height - 4);
      context.lineTo(x * width + 4, y * height);
      context.lineTo(x * width, y * height + 4);
      context.lineTo(x * width - 4, y * height);
      context.closePath();
      context.fill();
      context.stroke();
    }
  }
  const detail = variant.settlements[selected];
  if (detail.bestSite) {
    const [x, y] = sites[detail.bestSite];
    const settlement = data.settlements.find(item => item.id === selected);
    context.beginPath();
    context.moveTo(x * width, y * height);
    context.lineTo(settlement.x * width, settlement.y * height);
    context.strokeStyle = "#f7fff8";
    context.lineWidth = 5;
    context.stroke();
    context.strokeStyle = "#175748";
    context.lineWidth = 2;
    context.stroke();
    context.beginPath();
    context.arc(x * width, y * height, 5, 0, Math.PI * 2);
    context.fillStyle = "#175748";
    context.fill();
    context.strokeStyle = "white";
    context.stroke();
  }
}

function render() {
  const height = document.querySelector('input[name="height"]:checked').value;
  const spacing = document.querySelector('input[name="spacing"]:checked').value;
  const mode = document.querySelector('input[name="model"]:checked').value;
  activeCase = data.cases[height + "-" + spacing];
  variant = activeCase.variants[mode];
  document.querySelector("#reachable").textContent = variant.reachable;
  document.querySelector("#candidates").textContent = activeCase.candidates;
  document.querySelector("#links").textContent = variant.links;
  document.querySelector("#meter").replaceChildren(...data.settlements.map((_, index) => {
    const segment = document.createElement("i");
    segment.className = index < variant.reachable ? "on" : "";
    return segment;
  }));

  for (const settlement of data.settlements) {
    const marker = markerById.get(settlement.id);
    const reachable = variant.settlements[settlement.id].count > 0;
    marker.className = "marker " + (reachable ? "reached" : "unreached");
    marker.setAttribute("aria-label", settlement.name + (reachable ? ", reachable" : ", no passing link"));
    marker.setAttribute("aria-pressed", String(settlement.id === selected));
  }
  settlementSelect.value = selected;
  const settlement = data.settlements.find(item => item.id === selected);
  const detail = variant.settlements[selected];
  document.querySelector("#settlement-name").textContent = settlement.name;
  const reason = mode === "terrain_los" && activeCase.variants.fspl_only.settlements[selected].count > 0
    ? "At least one site passes the signal-strength check, but the terrain model blocks those paths."
    : "The assumed signal is too weak from the evaluated sites.";
  document.querySelector("#settlement-detail").textContent = detail.count
    ? detail.count + " candidate " + (detail.count === 1 ? "site has" : "sites have") +
      " a passing link. The map draws the passing link with the strongest signal."
    : "No candidate has a passing link here. " + reason;
  drawMap();
}

document.querySelectorAll(".choices input").forEach(input => input.addEventListener("change", render));
sitesToggle.addEventListener("change", drawMap);
settlementSelect.addEventListener("change", () => { selected = settlementSelect.value; render(); });
window.addEventListener("resize", drawMap);
render();
