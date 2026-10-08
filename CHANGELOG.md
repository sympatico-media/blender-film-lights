# Changelog

## Unreleased

- Reorganized the repository for public release: moved the asset library and its
  catalog file into `library/`, moved preview renders into `docs/images/`, removed
  development scripts and their intermediate output, and split licensing into
  GPL-3.0-or-later (research/build scripts) and CC BY 4.0 (the Blender assets).
- Diffusion materials updated from TRP/LEE/Rosco reference data (see
  `research/diffusion_calibration_2026-10-07/`). Eight transmitting fabrics
  updated in place; object controls, asset identifiers, and the Solid and
  Ultrabounce materials are unchanged.
- COB Light's Fresnel attachment now uses a native Blender Spot light instead of
  mesh emission, with an independent source-radius control for shadow softness.
- Panel Light now uses a native rectangular Area light at its front face instead
  of mesh emission, matching the panel's visible geometry and tilt.
- COB Light's reflector and octobox mounts are sealed to prevent light leaks.

## 1.0 — 2026-10-06

Initial release. Three procedural Blender assets: COB Light, Panel Light, and
Diffusion Frame.

- COB Light: Wattage, Kelvin/RGB color, COB diameter, and Bare / Reflector /
  Fresnel / Octobox attachments with fabric and grid options.
- Panel Light: width/height/depth, Kelvin/RGB color, front rim and egg-crate
  grid, yoke and tilt.
- Diffusion Frame: round/square/speed-rail frame types, ten fabric presets,
  and an optional pin.
- Validated in Blender 5.2.2 LTS: append into a factory-empty scene,
  independent modifier-control instances per asset, attachment and fabric
  toggles, and save/reload of imported assets.
