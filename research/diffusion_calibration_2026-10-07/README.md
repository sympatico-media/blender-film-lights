# Diffusion calibration research

Collected **7 October 2026** for Sympatico Lighting. Research only; no Blender materials or release files changed.

## Files

- [Measurements, CSV](reference_measurements.csv): source-specific calibration candidates, units, page numbers, and identity caveats.
- [Measurements, JSON](reference_measurements.json): the same records with explicit data conventions.
- [Source register](sources.json): URLs, access date, authority, and hashes of three locally saved PDFs.
- [Current shader baseline](current_shader_baseline.json): existing authored parameters, not real-world measurements.
- [Calibration notes](calibration_notes.md): interpretation, missing evidence, and a proposed validation procedure.
- [Source PDFs](sources/): original reference documents for future checks. These are third-party documents, are not redistributed with this repository, and must be downloaded from the URLs in `sources.json`.
- [`validation/`](validation/): `build_test_rig.py` and `fit_diffusion.py` are runnable (build the synthetic rig, then fit coefficients from its renders). `validation/test_materials.py` is a historical record of the before/after acceptance test; it depends on development-only files not included here and will not run as-is.

## Findings to act on

LEE provides published transmission values for [250](https://leefilters.com/colour/250-half-white-diffusion/) and [410 Opal](https://leefilters.com/colour/410-opal-frost/). The legacy manufacturer brochure also covers 215; its age is explicitly flagged in the dataset.

The [TRP test book](https://trpworldwide.com/wp-content/uploads/2025/06/Photometric-Full-FINAL_V2.pdf) supplies exposure, color, and shadow-wrap targets for the silk and muslin candidates. Full silk maps to polysilk and half silk to China silk in that manufacturer's terminology. Those are proposed identities for our generic presets, not claims that all suppliers' fabrics behave identically.

**Keep test contexts separate.** LEE's 250 specification lists 0.75 stop, its [M8 comparator](https://leefilters.com/lighting/diffusion-comparator/) shows 0.6 stop, and TRP measures 0.8 stop. These are different observations, not three numbers to average into a material.

Our Opal reference has been LEE 410. TRP's Rosco Opal entry is stored as an alternative identity only. Do not silently use it as LEE data.

No full spectral transmission curves, measured BSDF/BTDF distributions, or absolute hemispherical reflectance values were established in this search. That limits achievable calibration, especially for saturated RGB illumination.
