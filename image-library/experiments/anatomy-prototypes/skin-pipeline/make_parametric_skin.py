#!/usr/bin/env python3
"""Generate deterministic atlas-style skin layers for bases that fail AI generation.

This is a geometry-locked fallback. It does not redraw anatomy. It uses the
existing outline-derived interior mask, fills it with smooth warm skin shading,
and writes cache/<base>_gen.png for pipeline.py run <base> --reuse.
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

import pipeline


DEFAULT_TARGETS = [
    "03_upper-arm-anterior",
    "05_upper-arm-posterior",
    "07_head-anterior",
    "08_head-posterior",
    "09_chest-abdomen",
    "10_back",
    "11_foot-plantar",
    "12_foot-dorsal",
    "13_lower-leg-anterior",
    "15_thigh-anterior",
    "16_thigh-posterior",
    "17_shoulder-joint-posterior",
]

PRESETS = {
    "head": {
        "base": (235, 181, 145),
        "highlight_u": -0.10,
        "highlight": 20,
        "highlight_w": 0.42,
        "edge": 18,
        "noise": 1.2,
    },
    "torso": {
        "base": (235, 178, 137),
        "highlight_u": -0.05,
        "highlight": 30,
        "highlight_w": 0.34,
        "edge": 24,
        "noise": 1.8,
    },
    "limb": {
        "base": (236, 181, 139),
        "highlight_u": -0.03,
        "highlight": 34,
        "highlight_w": 0.20,
        "edge": 26,
        "noise": 1.8,
    },
    "foot": {
        "base": (235, 177, 137),
        "highlight_u": 0.0,
        "highlight": 28,
        "highlight_w": 0.30,
        "edge": 20,
        "noise": 1.5,
    },
}

BASE_PROFILE = {
    "07_head-anterior": "head",
    "08_head-posterior": "head",
    "09_chest-abdomen": "torso",
    "10_back": "torso",
    "11_foot-plantar": "foot",
    "12_foot-dorsal": "foot",
}


def profile_for(base):
    return PRESETS[BASE_PROFILE.get(base, "limb")]


def skin_layer(base, seed):
    bc = pipeline.CFG["bases"][base]
    img = pipeline.load_base(base)
    W, H = img.size
    box = bc.get("work_box") or pipeline.suggest_work_box(W, H, bc["open_sides"])[1]
    outline, _bones = pipeline.outline_and_bones(img, bc)
    interior, _seals = pipeline.interior_for(img, outline, bc)

    preset = profile_for(base)
    arr = np.ones((H, W, 3), dtype=np.float64) * 255
    rng = np.random.default_rng(seed)
    base_col = np.array(preset["base"], dtype=np.float64)

    for y in range(H):
        row = np.where(interior[y])[0]
        if row.size == 0:
            continue
        xmin, xmax = row.min(), row.max()
        center = (xmin + xmax) / 2
        half = max((xmax - xmin) / 2, 1)
        t = y / max(H - 1, 1)
        x = row.astype(np.float64)
        u = (x - center) / half

        color = base_col.copy()
        color += np.array([7, -2, -7], dtype=np.float64) * (0.5 - t)
        edge_shadow = -preset["edge"] * (np.abs(u) ** 1.7)
        central_high = preset["highlight"] * np.exp(-((u - preset["highlight_u"]) / preset["highlight_w"]) ** 2)
        central_high *= 0.78 + 0.22 * np.cos((t - 0.52) * np.pi)
        side_soft = 9 * np.exp(-((u - 0.45) / 0.40) ** 2)
        side_shadow = -8 * np.exp(-((u + 0.62) / 0.33) ** 2)
        joint_warm = 9 * np.exp(-((t - 0.08) / 0.08) ** 2) + 8 * np.exp(-((t - 0.92) / 0.07) ** 2)
        shade = edge_shadow + central_high + side_soft + side_shadow + joint_warm
        col = color[None, :] + shade[:, None]

        # Head/torso should not have a narrow shin-like highlight.
        if BASE_PROFILE.get(base) in ("head", "torso"):
            col[:, 0] += 4 * np.exp(-(u / 0.65) ** 2)
            col[:, 2] -= 2 * np.exp(-(u / 0.75) ** 2)
        else:
            col[:, 0] += 4 * np.exp(-((u - 0.15) / 0.55) ** 2)
            col[:, 2] -= 3 * np.exp(-((u + 0.15) / 0.70) ** 2)
        arr[y, row] = np.clip(col, 0, 255)

    noise = rng.normal(0, preset["noise"], (H, W))
    noise_img = Image.fromarray(np.uint8(np.clip(noise + 128, 0, 255))).filter(ImageFilter.GaussianBlur(5))
    noise = np.array(noise_img).astype(np.float64) - 128
    arr[interior] = np.clip(arr[interior] + noise[interior, None], 0, 255)
    full = Image.fromarray(arr.astype(np.uint8))
    return pipeline.apply_work_box(full, box).convert("RGB"), box, int(interior.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bases", nargs="*", default=DEFAULT_TARGETS)
    ap.add_argument("--seed", type=int, default=20260707)
    args = ap.parse_args()
    pipeline.CACHE.mkdir(exist_ok=True)
    for base in args.bases:
        gen, box, area = skin_layer(base, args.seed)
        out = pipeline.CACHE / f"{base}_gen.png"
        gen.save(out)
        print(f"{base}: wrote {out} size={gen.size} box={box} interior={area}")


if __name__ == "__main__":
    main()
