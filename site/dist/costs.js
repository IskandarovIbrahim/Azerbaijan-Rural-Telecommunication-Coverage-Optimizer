"use strict";

const costData = window.PILOT_DATA.costs;
const profileControl = document.querySelector("#cost-profile");
const costRows = document.querySelector("#cost-rows");
const usd = new Intl.NumberFormat("en-US", {
  style: "currency", currency: "USD", maximumFractionDigits: 0,
});
const percent = new Intl.NumberFormat("en-US", {
  style: "percent", maximumFractionDigits: 2,
});
const roundedUsd = amount => usd.format(Math.round(amount / 100) * 100);
const methods = ["minimum_count", "greedy", "exact"];

function renderCosts() {
  const key = profileControl.value;
  const profile = costData.profiles[key];
  document.querySelector("#cost-inputs").textContent =
    usd.format(profile.core_usd) + " setup per site · " + usd.format(profile.mast_usd["20"]) +
    " for a 20 m mast · " + usd.format(profile.mast_usd["40"]) +
    " for a 40 m mast · " + usd.format(profile.access_usd_per_km) + " per km from a mapped road";

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
      cell.textContent = roundedUsd(result.total_usd);
      cell.append(count);
      if (method === "exact") cell.className = "minimum-cost";
      row.append(cell);
    }
    return row;
  });
  costRows.replaceChildren(...rows);

  const denseTall = costData.cases.find(scenario =>
    scenario.mast_height_m === 40 && scenario.grid_spacing_m === 3000
  ).estimates[key];
  const saving = denseTall.minimum_count.total_usd - denseTall.exact.total_usd;
  const greedyGap = denseTall.greedy.total_usd - denseTall.exact.total_usd;
  const finding = document.querySelector("#cost-finding");
  finding.textContent = "At 40 m and 3 km spacing, minimum-cost selection reaches nine settlements for " +
    "about " + roundedUsd(denseTall.exact.total_usd) + ", a saving of about " + roundedUsd(saving) +
    " versus pricing the existing minimum-tower layout. " +
    (greedyGap > 0
      ? "Cost-aware greedy is about " + percent.format(greedyGap / denseTall.exact.total_usd) + " above the minimum."
      : "Cost-aware greedy matches the minimum.");
}

profileControl.addEventListener("change", renderCosts);
renderCosts();
