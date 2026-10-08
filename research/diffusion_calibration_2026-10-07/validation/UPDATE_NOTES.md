# Diffusion materials — reference-informed update, 7 October 2026

Eight transmitting materials updated in place. Frame and octobox share the same silk materials. Object controls, geometry, asset identifiers, Solid and Ultrabounce optical behavior are preserved.

The implementation separates direct transmission, diffuse transmission, and reflection. Per-channel energy allocations sum to at most one; the remainder represents absorption. Reflection allocations are retained from the authored materials and remain unmeasured. Fine bump affects reflection only.

Silk = TRP White Polysilk; Half Silk = TRP White China Silk; Quarter Silk = TRP White Quarter Silk. Muslins use TRP's corresponding fabrics. Exposure fitting uses TRP's recorded losses and least-squares 10/20-degree shadow readings. Published distance layout reproduced: source–fabric 3ft, fabric–flag 4ft, flag–wall 10ft, fabric/flag 4×4ft. The real fixture is approximated by an 80mm Lambertian area disk. Receiver sample chosen at x=-0.7m. Therefore this is NOT an exact recreation of the source's photometric test.

250 uses TRP's 0.8-stop observation; LEE's 0.75-stop specification and 0.6-stop comparator remain separate observations. 215 uses the legacy LEE 36% figure and Opal uses LEE410's 71% figure as receiver-ratio proxies in our rig. Those are not demonstrated hemispherical transmission values. Scattered fractions for these two gels are qualitative assumptions. No Rosco Opal measurements are substituted for LEE410.

RGB transmission tint approximates the ratio between Planckian-locus RGB colors at the reported output CCT and 3250K input, normalized to unit neutral-light luminance. This is a restrained color approximation, NOT spectral calibration. Duv and saturated RGB behavior are unmeasured. Unknown gel tint stays neutral.

The two-lobe model cannot reproduce the entire measured shadow curve. In particular muslin far-shadow spread remains too narrow in this rig; do not advertise exact softness matching. Full-silk/half-silk/quarter-silk names are material grades, not fractional stop losses. Fixture wattage remains uncalibrated against electrical input wattage.

See fit_parameters.json and render_validation.json beside the research notes for coefficients, measured render results, and residuals. OpenEXR files preserve scene-linear measurements. Original artistic versions are recoverable in Before_Reference_Diffusion_Update.blend.

Sources:
https://trpworldwide.com/wp-content/uploads/2025/06/Photometric-Full-FINAL_V2.pdf
https://leefilters.com/colour/250-half-white-diffusion/
https://leefilters.com/colour/410-opal-frost/
https://images.thomann.de/pics/prod/leefilters_folder.pdf
