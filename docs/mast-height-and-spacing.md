# Mast height and candidate spacing in the Quba pilot

We reran the same Xınalıq study with two antenna heights and two candidate grid spacings. All four runs kept the same 14 receiver points, 90 m terrain, radio power, frequency, antenna gains and screening rules. The 3 km grid includes all eligible locations from the 6 km grid. A candidate is a location the optimizer can choose from. The counts below show what is reachable across the whole candidate pool.

| Mast antenna height | Grid spacing | Eligible candidates | Usable terrain-aware links | Reachable settlements |
| ---: | ---: | ---: | ---: | ---: |
| 20 m | 6 km | 19 | 9 of 266 | 5 of 14 |
| 40 m | 6 km | 19 | 10 of 266 | 6 of 14 |
| 20 m | 3 km | 84 | 29 of 1,176 | 8 of 14 |
| 40 m | 3 km | 84 | 34 of 1,176 | 9 of 14 |

The denser grid added three reachable settlements at either height. The taller mast added one at either spacing, Zeyid. Together the changes increased reachability from about 36% to 64%. Haputlu, Əlik and Şeyx Şamil gained a usable link from denser siting. Laza, Adur, Qrızdəhnə, Aladaş and Kuzun remain unreachable in all four runs.

These results use the geometric line-of-sight and hypothetical radio assumptions in the [radio model](radio-model.md). They compare candidate pools before site selection. No height-dependent construction costs were modeled. The 40 m/3 km matrix can be used for a reachable-only optimizer comparison. Full cover is infeasible for this matrix because five settlement columns are all zero.

## Reproduce the comparison

From the project root in PowerShell, with the geodata dependencies and the [pinned inputs cached](pilot-inputs.md):

```powershell
.\.venv\Scripts\python.exe scripts/compare_mast_height_and_spacing.py
```

Open `outputs/quba-height-spacing/comparison.json` for all four results. Each case subfolder holds its actual config, link diagnostics, coverage matrices and summary. The script uses separate output folders and leaves the original pilot files in place.
