# Pilot radio-link model

Run the comparison from the VS Code PowerShell terminal after [preparing the pilot](pilot-inputs.md):

```powershell
.\.venv\Scripts\coverage-optimizer.exe model-links
```

## What the model checks

Each eligible candidate site is paired with one receiver point per settlement. Both variants use the same one-way link budget and projected horizontal distance. Free-space path loss uses the ITU formula with distance in kilometers and frequency in MHz. The received signal power minus the receiver threshold and fade margin must be at least zero. The terrain variant also requires a clear direct ray. [ITU-R P.525-5](https://www.itu.int/rec/R-REC-P.525-5-202411-I/en)

The [pilot config](../config/quba-pilot.json) assumes 900 MHz, 23 dBm transmit power, 8 dBi transmit and 3 dBi receive gain, 2 dB system loss, 20 m transmit and 4 m receive heights, a −100 dBm receiver threshold, and a 15 dB fade margin. These values define a hypothetical fixed-wireless downlink. The scenario assumes power and backhaul at each candidate site.

The visibility check adds antenna heights to their endpoint raster cells and checks every cell crossed by the direct ray. Each cell has a constant surface height. The geometric Earth-curvature correction uses an effective Earth radius of 4/3 of the mean Earth radius. Zero clearance is classified as blocked. A terrain gap makes the visibility test unknown. A link with insufficient signal margin is unusable regardless of its visibility. [ITU-R P.530-19](https://www.itu.int/rec/R-REC-P.530-19-202509-I/en)

The 90 m surface grid can miss narrow obstructions or make steep cell boundaries look sharper than they are. The geometric test omits Fresnel clearance, diffraction, interference, return-link performance and field calibration. These results describe the modeled links for this pilot.

## First pilot run

| Model | Usable links out of 266 | Settlements reachable from at least one candidate out of 14 |
| --- | ---: | ---: |
| Free-space path loss only | 179 | 14 |
| Free-space path loss plus terrain line of sight | 9 | 5 |

Of the 179 links that passed the signal test, 170 were blocked by the modeled terrain. Nine settlements have no usable link from the current candidate set, so requiring all 14 to be covered is infeasible under this scenario. The optimizer should report that condition and can also compare methods on the explicitly reachable subset.

Open `outputs/quba-links/summary.json` for the counts and settlement names. `links.csv` holds one row per pair per variant. `matrix.json` holds the two binary matrices with identical site and settlement ordering, plus site costs and settlement weights. Rows are sites and columns are settlements. Only usable links have a value of 1. The files can be regenerated from the prepared inputs and stay local.

## Mast-height and site-density comparison

See the [four-case experiment](mast-height-and-spacing.md) for the effect of 40 m masts and a 3 km candidate grid.
