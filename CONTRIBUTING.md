# Contributing

## Observation pull requests

1. Export the truth bundle from Pod Hammer's Launch Stats screen.
2. Review the JSON. It must contain no secret or connection information.
3. Add it under `observations/YYYY/MM/` using its `run_id` as the filename.
4. Run `python3 scripts/validate.py`.
5. Open a pull request and affirm that publication is intentional.

One file represents one launch attempt. Do not combine or edit durations to
make a run look better. Failed and capacity-constrained attempts are valuable.

## Recipe pull requests

A recipe must pin public artifacts by immutable revision and identify its
bootstrap SHA-256. It must include readiness checks and describe compatible
provider GPU SKUs without claiming that inventory is guaranteed.

Recipe status progresses as follows:

1. `experimental`
2. `community-tested`
3. `verified`
4. `deprecated`

Only maintainers promote a recipe to `verified`, based on repeatable evidence.

## Generated data

Do not edit `aggregates/summary.json` manually. The validation workflow rebuilds
it and fails if the result is not reproducible.
