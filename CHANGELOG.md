# Changelog

## v3.5.1 — 2026-10-31

Integrated [MehranAkbarii's pull request #8](https://github.com/iammrmikemanmods/gta-iv-grass-fix/pull/8), resolving the README deletion conflict by retaining the current project page.

- Changed the supplied `DistanceMultiplier` from `1.25` to `1.00`.
- Changed `SpawnsPerUpdate` from `128` to `1024`.
- Kept the procedural, rendered-object, and provider capacities at `16384`, `8192`, and `40`, with neutral density multipliers.
- Updated INI comments to warn about instability and micro-stutters above 1.0 and experimental distance values above 2.0.
- Updated the main README to match every active setting in the supplied INI and the v3.5.1 compatibility warning: do not combine this release with Props Restoration or Restored Vegetation.
- Fixed all six README screenshots by moving them into `assets/grass-fix/`; replaced the duplicate project description under `assets/` with an image index.

This PR changes configuration and documentation; it does not change the C runtime source. The release ZIP is the existing [v3.5.1 package published by MehranAkbarii](https://github.com/MehranAkbarii/gta-iv-grass-fix/releases/tag/v3.5.1), preserved without rebuilding or repacking.

Release archive SHA-256: `c28be1898c77dbed480da4ef3a93bf8d6822bce0072d55881b7a45385a5a4901`.
