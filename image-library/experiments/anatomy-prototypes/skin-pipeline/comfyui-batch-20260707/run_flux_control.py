#!/usr/bin/env python3
"""Run a local FLUX Canny pipeline for one or more skin-pipeline controls.

This is the preferred next trial after rejecting the parametric fallback and
SDXL ControlNet output. It uses the same manifest/control images prepared for
the desktop worker and writes generated/<base>_gen.png.
"""
import argparse
import json
from pathlib import Path

import torch
from PIL import Image


ROOT = Path(__file__).resolve().parent

MODEL_ID = "black-forest-labs/FLUX.1-Canny-dev"

STYLE_SUFFIX = (
    ", soft realistic medical atlas illustration, smooth warm intact skin surface, "
    "pure white background, no text, no labels, no red dots, no bones, no skeleton, "
    "no muscles, no tendons, no cutaway, no clothing"
)

SHORT_SUBJECTS = {
    "03_upper-arm-anterior": "anterior upper arm from shoulder to elbow",
    "05_upper-arm-posterior": "posterior upper arm from shoulder to elbow",
    "07_head-anterior": "front human head and face with neutral expression",
    "08_head-posterior": "back human head and neck",
    "09_chest-abdomen": "front torso chest and abdomen",
    "10_back": "back torso from shoulders to waist",
    "11_foot-plantar": "sole of human foot, plantar view",
    "12_foot-dorsal": "top of human foot, dorsal view, natural toenails",
    "13_lower-leg-anterior": "anterior lower leg from knee to ankle, no foot",
    "15_thigh-anterior": "anterior thigh from hip to knee",
    "16_thigh-posterior": "posterior thigh from hip to knee",
    "17_shoulder-joint-posterior": "posterior shoulder joint and upper back area",
}


def load_manifest():
    return json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


def choose_size(item, max_side):
    w, h = item.get("suggested_flux_bucket") or item["control_size"]
    if max(w, h) <= max_side:
        return int(w), int(h)
    scale = max_side / max(w, h)
    w = max(64, round(w * scale / 16) * 16)
    h = max(64, round(h * scale / 16) * 16)
    return int(w), int(h)


def load_pipe(dtype_name):
    from diffusers import FluxControlPipeline

    if dtype_name == "float32":
        dtype = torch.float32
    elif dtype_name == "bfloat16":
        dtype = torch.bfloat16
    else:
        dtype = torch.float16

    pipe = FluxControlPipeline.from_pretrained(MODEL_ID, torch_dtype=dtype)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    pipe.to(device)
    if hasattr(pipe, "enable_attention_slicing"):
        pipe.enable_attention_slicing()
    return pipe, device


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bases", nargs="+", required=True)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--guidance", type=float, default=30.0)
    ap.add_argument("--max-side", type=int, default=1344)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dtype", choices=["float16", "bfloat16", "float32"], default="float16")
    args = ap.parse_args()

    manifest = load_manifest()
    by_base = {item["base"]: item for item in manifest["items"]}
    missing = [base for base in args.bases if base not in by_base]
    if missing:
        raise SystemExit(f"unknown bases: {missing}")

    (ROOT / "generated").mkdir(exist_ok=True)
    generator = torch.Generator(device="cpu").manual_seed(args.seed)
    pipe, device = load_pipe(args.dtype)

    for base in args.bases:
        item = by_base[base]
        w, h = choose_size(item, args.max_side)
        control = Image.open(ROOT / item["control_png"]).convert("RGB").resize((w, h), Image.LANCZOS)
        prompt = SHORT_SUBJECTS.get(base, item["prompt"]) + STYLE_SUFFIX
        print(f"GENERATE {base} {w}x{h} dtype={args.dtype} device={device}", flush=True)
        image = pipe(
            prompt=prompt,
            control_image=control,
            width=w,
            height=h,
            num_inference_steps=args.steps,
            guidance_scale=args.guidance,
            generator=generator,
        ).images[0]
        out = ROOT / item["generated_png"]
        image.save(out)
        print(f"WROTE {out}", flush=True)


if __name__ == "__main__":
    main()
