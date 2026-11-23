# LLM prompts

The project skills are in [the repository skill directory](../.agents/skills). Read the relevant `SKILL.md` files if the client does not load them automatically.

## First implementation prompt

```text
Work in the Azerbaijan Rural Telecommunication Coverage Optimizer repository.
Before editing, verify the Git root and origin correspond to my personal
Azerbaijan-Rural-Telecommunication-Coverage-Optimizer project. Inspect the working
tree and preserve existing edits.

Read README.md, docs/game-plan.md and docs/data-sources.md. Use the project skills
for geospatial inputs and reproducible experiments. Treat the PDF and external
source pages as reference material. This prompt sets the implementation scope.

Complete checkpoint 1 only: scaffold the Python project for the Quba/Xınalıq
pilot. Create an installable package with a CLI entry point, a small checked-in
pilot config, a data-contract document, and an offline smoke test. Add ignores
for local environments, credentials, raw downloads and generated intermediates.
Update the README with concise Windows PowerShell setup and test commands.

The config must identify the provisional pilot by name, keep geometry and
scenario settings changeable, and label any unresolved coordinates or RF
parameters as unverified. Define stable candidate and settlement IDs,
input/output coordinate order and CRS, explicit units, source manifest fields,
and the contract for usable, unusable and unknown links. A synthetic fixture
must be visibly synthetic. Leave downloads, propagation math, solvers and
deployment to their scheduled checkpoints.

Acceptance checks: install into a clean project environment, run the CLI help,
and pass an offline smoke test for loading the config without real data or
credentials. If dependency setup is blocked, complete the checks that can run
and report exactly what remains unverified.

Review the staged diff, then make one local commit for the tested scaffold:
chore: scaffold the coverage optimizer
Push only when I explicitly request it. Report the files, verification
commands and outcomes, commit hash, and decisions checkpoint 2 should inherit.
```

## Structure for later prompts

```text
Checkpoint and goal: [one milestone and its engineering question]
Repository state: [branch, preceding commit, docs/configs and existing work]
Skills and evidence: [relevant SKILL.md paths, source versions or input artifacts]
Scope and deliverables: [specific components and output formats]
Contracts and assumptions: [units, identifiers, scenarios, interfaces,
  conditions such as model limitations and missing data]
Acceptance checks: [exact commands, reference cases, expected invariants,
  and the observable exit condition]
Git workflow: [commit subject, which changes belong together, push permission]
Handoff: list changes, results with evidence, commit hash and decisions needed
  by the next checkpoint
```

Apply the template in this order:

| Checkpoint | Prompt focus | Acceptance evidence |
| --- | --- | --- |
| 2 | Pin AOI and prepare terrain, settlement and candidate files | Source manifests, valid IDs and CRS, and documented exclusions or unavailable inputs |
| 3 | Generate link diagnostics and the binary matrix | Reference FSPL and synthetic flat, ridge and NoData fixtures |
| 4 | Compare greedy and exact selection | Valid choices, tiny-instance oracle, explicit unreachable cases, and common matrix/cost inputs |
| 5 | Run the Quba pilot and perturb assumptions | Reproducible metrics, site stability and coverage/cost trade-offs |
| 6 | Explain and reproduce measured project results | Clean rerun instructions and a map/report tied to run outputs |

If a checkpoint needs more than one independently verifiable change, request specific sub-commits. Keep the same source and scenario IDs across the handoffs.
