"use strict";

const costArea = document.querySelector("#study-area");
const profileControl = document.querySelector("#cost-profile");
const costRows = document.querySelector("#cost-rows");
const aznPerUsd = 1.7;
const number = new Intl.NumberFormat("en-US", {maximumFractionDigits: 0});
const formatAzn = amount => number.format(amount) + " AZN";
const aznFromUsd = amount => formatAzn(amount * aznPerUsd);
const roundedAzn = amount => formatAzn(Math.round(amount * aznPerUsd / 100) * 100);
const methods = ["minimum_count", "greedy", "exact"];

function renderCostEstimate() {
  const height = Number(document.querySelector('input[name="height"]:checked').value);
  const spacing = Number(document.querySelector('input[name="spacing"]:checked').value);
  const costData = window.PILOT_DATA.areas[costArea.value].costs;
  const profile = profileControl.value;
  const scenario = costData.cases.find(item =>
    item.mast_height_m === height && item.grid_spacing_m === spacing * 1000
  );
  const estimate = scenario.estimates[profile].exact;
  const towers = estimate.site_count === 1 ? " tower" : " towers";
  document.querySelector("#estimate-scenario").textContent =
    height + " m mast · " + spacing + " km candidate grid · " + costData.profiles[profile].label;
  document.querySelector("#estimate-price").textContent = roundedAzn(estimate.total_usd);
  document.querySelector("#estimate-coverage").textContent =
    estimate.site_count + towers + " · " + scenario.reachable_count + " of " +
    scenario.settlement_count + " settlements reachable";
}

function renderCosts() {
  renderCostEstimate();
  const costData = window.PILOT_DATA.areas[costArea.value].costs;
  const key = profileControl.value;
  const profile = costData.profiles[key];
  document.querySelector("#cost-inputs").textContent =
    aznFromUsd(profile.core_usd) + " setup per site · " + aznFromUsd(profile.mast_usd["20"]) +
    " for a 20 m mast · " + aznFromUsd(profile.mast_usd["40"]) +
    " for a 40 m mast · " + aznFromUsd(profile.access_usd_per_km) + " per km from a mapped road";

  const rows = costData.cases.map(scenario => {
    const row = document.createElement("tr");
    const name = document.createElement("th");
    name.scope = "row";
    name.textContent = scenario.mast_height_m + " m · " + scenario.grid_spacing_m / 1000 + " km";
    row.append(name);
    const reachable = document.createElement("td");
    reachable.textContent = scenario.reachable_count + " of " + scenario.settlement_count;
    row.append(reachable);
    for (const method of methods) {
      const result = scenario.estimates[key][method];
      const cell = document.createElement("td");
      const count = document.createElement("span");
      count.className = "cost-site-count";
      count.textContent = result.site_count + (result.site_count === 1 ? " tower" : " towers");
      cell.textContent = roundedAzn(result.total_usd);
      cell.append(count);
      if (method === "exact") cell.className = "minimum-cost";
      row.append(cell);
    }
    return row;
  });
  costRows.replaceChildren(...rows);
}

for (const input of document.querySelectorAll('input[name="height"], input[name="spacing"]')) {
  input.addEventListener("change", renderCostEstimate);
}
profileControl.addEventListener("change", renderCosts);
costArea.addEventListener("change", renderCosts);
renderCosts();
