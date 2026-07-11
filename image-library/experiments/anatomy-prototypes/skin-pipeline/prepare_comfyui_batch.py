#!/usr/bin/env python3
"""Prepare ControlNet/ComfyUI handoff assets for the skin pipeline.

The generated controls use the exact same outline extraction and work_box logic
as pipeline.py. Generated images from ComfyUI should be saved back as
cache/<base>_gen.png, then post-processed with:

    python3 pipeline.py run <base> --reuse
"""
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

import pipeline


HERE = Path(__file__).parent
OUT = HERE / "comfyui-batch-20260707"

USABLE_ON_20260707 = {
    "01_hand-palmar",
    "02_hand-dorsal",
    "04_forearm-anterior",
    "06_forearm-posterior",
    "14_lower-leg-posterior",
}


README = """# ComfyUI Batch Handoff - Skin Pipeline

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
"""


def prompt_for(base_cfg):
    return base_cfg.get("prompt") or pipeline.cfgv(
        base_cfg, "prompt_template"
    ).format(subject=base_cfg["subject"])


def target_bases():
    for base, bc in pipeline.CFG["bases"].items():
        if bc.get("skip") or base in USABLE_ON_20260707:
            continue
        yield base, bc


def make_sheet(items):
    thumbs = []
    for item in items:
        src = Image.open(OUT / item["source_png"]).convert("RGB")
        ctrl = Image.open(OUT / item["control_png"]).convert("RGB")
        src.thumbnail((260, 260))
        ctrl.thumbnail((260, 260))
        tile = Image.new("RGB", (560, 330), "white")
        tile.paste(src, (10, 40))
        tile.paste(ctrl, (290, 40))
        d = ImageDraw.Draw(tile)
        d.text((10, 10), item["base"], fill=(0, 0, 0))
        d.text((10, 305), "source", fill=(80, 80, 80))
        d.text((290, 305), "control", fill=(80, 80, 80))
        thumbs.append(tile)

    if not thumbs:
        return
    cols = 2
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 560, rows * 330), "white")
    for i, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((i % cols) * 560, (i // cols) * 330))
    sheet.save(OUT / "review_contact_sheet.png")


def main():
    for sub in ("control", "source", "prompts", "generated"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)

    items = []
    for base, bc in target_bases():
        img = pipeline.load_base(base)
        W, H = img.size
        box = bc.get("work_box")
        bucket = None
        if not box:
            sug = pipeline.suggest_work_box(W, H, bc["open_sides"])
            if not sug:
                raise SystemExit(f"{base}: no usable work_box")
            box = sug[1]
            bucket = sug[2]

        outline, _bones = pipeline.outline_and_bones(img, bc)
        ctrl = pipeline.apply_work_box(outline, box).convert("RGB")

        source_png = OUT / "source" / f"{base}_source.png"
        control_png = OUT / "control" / f"{base}_control.png"
        prompt_txt = OUT / "prompts" / f"{base}.txt"

        shutil.copy2(pipeline.BASES_DIR / f"{base}.png", source_png)
        ctrl.save(control_png)
        prompt = prompt_for(bc)
        prompt_txt.write_text(prompt + "\n", encoding="utf-8")

        items.append({
            "base": base,
            "source_png": str(source_png.relative_to(OUT)),
            "control_png": str(control_png.relative_to(OUT)),
            "prompt_txt": str(prompt_txt.relative_to(OUT)),
            "generated_png": f"generated/{base}_gen.png",
            "cache_destination": f"cache/{base}_gen.png",
            "original_size": [W, H],
            "work_box": box,
            "control_size": list(ctrl.size),
            "suggested_flux_bucket": list(bucket) if bucket else None,
            "open_sides": bc["open_sides"],
            "outline_thresh": pipeline.cfgv(bc, "outline_thresh"),
            "prompt": prompt,
        })

    manifest = {
        "created_for": "TungsAcu-DB skin-pipeline desktop ComfyUI handoff",
        "output_contract": "Save generated/<base>_gen.png, copy to skin-pipeline/cache/<base>_gen.png, then run pipeline.py run <base> --reuse.",
        "usable_existing_outputs": sorted(USABLE_ON_20260707),
        "items": items,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text(README, encoding="utf-8")
    make_sheet(items)
    print(f"wrote {len(items)} targets to {OUT}")


if __name__ == "__main__":
    main()
