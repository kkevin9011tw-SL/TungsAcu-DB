# ComfyUI Batch Handoff - Skin Pipeline

Purpose: use a desktop ComfyUI/ControlNet workflow to generate only the skin
texture layer, while keeping the original WHO geometry and acupuncture JSON
coordinates locked to the existing base images.

## Inputs

- `control/*_control.png`: black/white outline control image after the same
  `work_box` transform used by `pipeline.py`.
- `source/*_source.png`: original clean WHO-style base for visual reference.
- `prompts/*.txt`: one prompt per base.
- `manifest.json`: sizes, work boxes, open sides, and output naming contract.

## Required ComfyUI Behavior

Use each `control/*_control.png` as a Canny/LineArt/SoftEdge ControlNet input.
Generate a soft clinical atlas skin surface on white background. Do not include
red points, labels, rulers, callouts, or bones in the generated image.

The generated PNG may be a different pixel size, but its aspect ratio must match
the control image. `pipeline.py` will resize it back into the original coordinate
system during `--reuse` post-processing.

## Output Contract

Save generated images as:

```text
generated/<base>_gen.png
```

Then copy each generated image back to the laptop repo as:

```text
assets/anatomy-prototypes/skin-pipeline/cache/<base>_gen.png
```

Finally run, from `assets/anatomy-prototypes/skin-pipeline/`:

```bash
rtk python3.12 pipeline.py run <base> --reuse
```

The final file will be:

```text
output/<base>_final.png
```

## First Targets

The user has marked these existing outputs as usable:
`01_hand-palmar`, `02_hand-dorsal`, `04_forearm-anterior`,
`06_forearm-posterior`, `14_lower-leg-posterior`.

This package focuses on the remaining non-skeleton bases:
`03`, `05`, `07`, `08`, `09`, `10`, `11`, `12`, `13`, `15`, `16`, `17`.
