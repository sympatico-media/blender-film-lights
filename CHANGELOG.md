# Changelog

## 1.4.0 — 2026-11-11

- Matched COB and panel yoke rotation handles to the C-Stand: visible world-space
  dials, with the COB dial at its side handle and a larger panel dial. Both
  use an editable angle conversion. Kit tilt now belongs to the fixture so
  its handle works directly; the stand retains height and pan.

- Moved the COB yoke into the fixture, with a Yoke toggle, Tilt control, and
  viewport dial. Native sources follow the head; stand kits use the same fixture.

- Added Combo Stand + COB Light and Combo Stand + Panel Light collection assets,
  with height-following mounts, fixture pan/tilt controls, independent light
  drivers, and Asset Browser previews. Stand height and pan are available
  on the stand; tilt is on the fixture, with viewport handles. Both kits prefer Append
  on drag-and-drop, matching the editable C-Stand + Fabric assembly.

- IES profiles now automatically select Bare, Reflector, or Fresnel geometry.
  Manual attachment and Fresnel beam settings are bypassed while IES is active
  and restored by selecting Default.

- Added the COB Light Profile dropdown: Default plus six bundled STORM 1200x
  IES distributions, using a dedicated native Point source with IES Texture nodes.
- Preserved Default attachment lighting and added a local IES installer and
  render regression test. The six manufacturer IES files are bundled externally
  under library/ies/ with attribution, outside the project’s CC BY/GPL licenses.

## 1.3.0 — 2026-11-09

- Native Blender lights now provide COB illumination in every attachment mode:
  disk Area sources for Bare and Octobox, Spot sources for Reflector and Fresnel.
- The visible COB mesh no longer contributes illumination. Fresnel power mapping
  is preserved; other modes change brightness/distribution and need exposure review.
- Added an existing-scene upgrade script and a Cycles regression test for native-only
  illumination, valid drivers, and Ultrabounce response across all four modes.

## 1.2.0 — 2026-11-09

- Added a procedural C-Stand with height and riser controls, optional grip head and boom arm, arm positioning, and a sandbag toggle.
- Added a Combo Stand with staged riser extension and a sandbag toggle.
- Added a C-Stand + Fabric collection combining a mounted stand, fabric, and boom mount, with flag tilt controls.
- Added the Sympatico/Grip asset catalog category.
- Added documentation for the Diffusion Frame's Mount at Pin control and for importing and duplicating complete assemblies.

## 1.1.1 — 2026-10-08

- Cleaned up the geometry node trees behind each fixture: simplified and
  reorganized the node networks with no change to asset controls or
  behavior.

## 1.1.0 — 2026-10-08

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
