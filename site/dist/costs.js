"use strict";

const costArea = document.querySelector("#study-area");
const profileControl = document.querySelector("#cost-profile");
const costRows = document.querySelector("#cost-rows");
const aznPerUsd = 1.7;
const number = new Intl.NumberFormat("en-US", {maximumFractionDigits: 0});
const formatAzn = amount => number.format(amount) + " AZN";
const aznFromUsd = amount => formatAzn(amount * aznPerUsd);
const percent = new Intl.NumberFormat("en-US", {
  style: "percent", maximumFractionDigits: 2,
});
const roundedAzn = amount => formatAzn(Math.round(amount * aznPerUsd / 100) * 100);
const methods = ["minimum_count", "greedy", "exact"];

function renderCosts() {
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

  const denseTall = costData.cases.find(scenario =>
    scenario.mast_height_m === 40 && scenario.grid_spacing_m === 3000
  );
  const estimates = denseTall.estimates[key];
  const saving = estimates.minimum_count.total_usd - estimates.exact.total_usd;
  const greedyGap = estimates.greedy.total_usd - estimates.exact.total_usd;
  const finding = document.querySelector("#cost-finding");
  finding.textContent = "At 40 m and 3 km spacing, minimum-cost selection reaches " + denseTall.reachable_count + " settlements for " +
    "about " + roundedAzn(estimates.exact.total_usd) + ", a saving of about " + roundedAzn(saving) +
    " versus pricing the existing minimum-tower layout. " +
    (greedyGap > 0
      ? "Cost-aware greedy is about " + percent.format(greedyGap / estimates.exact.total_usd) + " above the minimum."
      : "Cost-aware greedy matches the minimum.");
}

profileControl.addEventListener("change", renderCosts);
costArea.addEventListener("change", renderCosts);
renderCosts();
