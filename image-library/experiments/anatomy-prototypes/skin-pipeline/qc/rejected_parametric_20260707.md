# Rejected Parametric Skin Trial - 2026-07-07

Status: rejected by user.

Reason:
- The deterministic/parametric skin layer preserves geometry but looks visibly artificial.
- It should not be used as a production base-map style.
- Do not treat `qc/review_parametric_20260707.png` as an approval sheet.

Next direction:
- Stop tuning the parametric fill method for visual quality.
- Use a high-quality controlled generative model instead, preferably local FLUX/Canny on the desktop worker, so geometry remains constrained while the rendered surface keeps the softer atlas style seen in the successful FLUX outputs.
