# How to use this evidence

## Evidence and limits

The measurements are calibration candidates, not ready-to-use shader coefficients. Matching one meter reading can hide the wrong scattering behavior. A material that scatters more light away from the meter can show greater stop loss without absorbing that same fraction of total energy.

TRP uses a 4×4 test diffusion and a 4×4 obstruction with an open-eye 2K source; the diffusion baseline is 11.3 EV and 3250 K. Consult the diagram on PDF page 8 and definition on page 9 before building a matching rig. Wrap Factor measures shadow falloff, not an intrinsic scattering angle. Full geometry dimensions have not yet been transcribed or independently reproduced. Ultrabounce uses a separate bounce test baseline, so its exposure reduction is not an albedo value. [TRP](https://trpworldwide.com/wp-content/uploads/2025/06/Photometric-Full-FINAL_V2.pdf)

Rosco explicitly demonstrates placement dependence: its Filter Facts page 21 measures beam center with source-to-subject distance 10 feet, with material either at the lamp or 3 feet forward. For Rosco 3010 Opal Tough Frost it reports 42% at the source versus 51% at 3 feet; these are comparator evidence, not LEE 410 targets. The same guide distinguishes spun diffusion's comparatively narrow spread from white diffusion's broader spread. [Rosco](https://us.rosco.com/sites/default/files/content/resource/2022-10/Rosco_FilterFacts09_22.pdf)

LEE 250 lists Y=60%, about 3/4 stop, and an absorption field of 0.22 under Source C. Do not interpret that 0.22 as 22% energy absorption: numerically it matches optical density, -log10(0.60)≈0.222. The page does not establish the full measurement acceptance geometry. Its 6774 K label is the source condition, not evidence of an output color shift. The same caution applies to LEE 410's source label. [LEE250](https://leefilters.com/colour/250-half-white-diffusion/) · [LEE410](https://leefilters.com/colour/410-opal-frost/)

The legacy LEE brochure is manufacturer-authored but distributor-hosted; the 215 row is on PDF page 36. Current LEE 215 product-page retrieval failed. Confirm current material specification before claiming a branded reproduction. [Brochure](https://images.thomann.de/pics/prod/leefilters_folder.pdf)

The white-front/black-back design of Ultrabounce is supported by its [manufacturer description](https://trpworldwide.com/west/product/black-white-ultrabounce-2/). Its absolute reflectance and reverse-side absorption remain unmeasured here. Generic Solid also needs a specific reference fabric.

## Interpretation rules

- Convert positive stop loss L to a meter response ratio with 2^(-L). This is a derived quantity, never a measured hemispherical transmission value.
- Fit direct transmission, scattered transmission, reflection, and absorption jointly. Keep energy accounting bounded. Do not equate the existing Mix Shader factor with a stop-loss target.
- A CCT change alone cannot determine RGB filter color, spectral transmission, or green/magenta shift. Published mired shifts may seed a white-light approximation; extrapolation across source temperatures remains an assumption. RGB/saturated-light behavior requires spectral evidence.
- Do not force full/half/quarter silk into a simple numeric progression. Name a supplier and material construction for each preset.
- Do not use LEE 228 or Rosco 3011 directional silk filters as substitutes for woven silk fabrics.
- Total output calibration of the fixtures is a separate task. The existing wattage control is not a verified electrical-power-to-light-output model.

## Proposed implementation and validation (not executed)

1. Freeze existing presets and save a versioned calibrated variant so visual changes remain reviewable.
2. Select exact product identities. Use the candidate mappings in the dataset; retain any unresolved mapping in documentation.
3. Rebuild a published test geometry at real scale. Fix source distribution, meter position/orientation, diffusion distance, frame size, obstruction, and surroundings. Obtain missing setup dimensions before calling it a reproduction.
4. Render unfiltered and filtered cases in Cycles to scene-linear EXR. Compare a defined receiver's luminance using identical settings. Stop loss is -log2(filtered/unfiltered). Exclude display tone mapping from measurements.
5. Fit exposure and shadow profiles together. A measured shadow profile constrains the model beyond a single central brightness value. If the current transparent/translucent blend cannot match both, change the scattering model rather than compensating only with brightness.
6. Test another source distance, incidence angle, fabric size, and white-light temperature. Reserve these as validation cases rather than fitting every case independently.
7. For bounce, compare a known diffuse reference in controlled geometry. Estimate reflectance separately from transmission.
8. Save targets, measured results, uncertainty, render settings, and residual differences. Only claim manufacturer-informed calibration until physical sample measurements support stronger claims.

## Remaining research

Request source setup dimensions and measurement uncertainty; spectral transmission/reflection data; angular scattering data or raw shadow profiles; daylight color measurements; exact silk weave/weight; and absolute Ultrabounce reflectance. None of those quantities should be invented from a product name or a thumbnail.
