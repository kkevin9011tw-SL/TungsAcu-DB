#!/usr/bin/env python3
"""Run local diffusers ControlNet generation for the skin-pipeline batch.

This is the SSH/scriptable alternative to driving ComfyUI manually. It consumes
manifest.json from this directory and writes generated/<base>_gen.png.
"""
import argparse
import json
from pathlib import Path

import torch
from PIL import Image


ROOT = Path(__file__).resolve().parent
NEGATIVE_PROMPT = (
    "photo, photorealistic, macro skin, pores, hair, muscles, tendons, exposed anatomy, "
    "cutaway, dissection, bones, skeleton, x-ray, text, labels, dots, ruler, clothing, "
    "gray background, shadow, deformity"
)

STYLE_SUFFIX = (
    ", intact skin surface only, 2D clinical atlas illustration, smooth airbrushed warm skin, "
    "low detail, pure white background"
)

SHORT_SUBJECTS = {
    "03_upper-arm-anterior": "cropped anterior upper arm from shoulder to elbow, no forearm, no hand",
    "05_upper-arm-posterior": "cropped posterior upper arm from shoulder to elbow, no forearm, no hand",
    "07_head-anterior": "front human head and face, short hair, neutral expression",
    "08_head-posterior": "back human head and neck, short hair",
    "09_chest-abdomen": "front torso chest and abdomen, no arms",
    "10_back": "back torso from shoulders to waist",
    "11_foot-plantar": "sole of human foot, plantar view",
    "12_foot-dorsal": "top of human foot, dorsal view, natural toenails",
    "13_lower-leg-anterior": "cropped anterior lower leg from knee to ankle, no foot, no toes",
    "15_thigh-anterior": "cropped anterior thigh from hip to knee, no lower leg, no foot",
    "16_thigh-posterior": "cropped posterior thigh from hip to knee, no lower leg, no foot",
    "17_shoulder-joint-posterior": "posterior shoulder joint and upper back area",
}

EXTRA_NEGATIVE = {
    "13_lower-leg-anterior": ", foot, toes",
    "15_thigh-anterior": ", lower leg, foot, toes",
    "16_thigh-posterior": ", lower leg, foot, toes",
    "03_upper-arm-anterior": ", forearm, hand, fingers",
    "05_upper-arm-posterior": ", forearm, hand, fingers",
}


PROFILES = {
    "sdxl-canny": {
        "base": "stabilityai/stable-diffusion-xl-base-1.0",
        "controlnet": "diffusers/controlnet-canny-sdxl-1.0",
        "class": "sdxl",
        "steps": 28,
        "guidance": 6.5,
        "control_scale": 0.82,
    },
    "sd15-canny": {
        "base": "runwayml/stable-diffusion-v1-5",
        "controlnet": "lllyasviel/sd-controlnet-canny",
        "class": "sd15",
        "steps": 28,
        "guidance": 7.5,
        "control_scale": 1.0,
    },
}


def load_manifest():
    return json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


def choose_size(item, max_side):
    size = item.get("suggested_flux_bucket") or item["control_size"]
    w, h = size
    if max(w, h) <= max_side:
        return int(w), int(h)
    scale = max_side / max(w, h)
    w = round(w * scale / 8) * 8
    h = round(h * scale / 8) * 8
    return max(64, int(w)), max(64, int(h))


def load_pipe(profile_name):
    profile = PROFILES[profile_name]
    # MPS + SDXL fp16 VAE can decode to NaNs/black images on this workflow.
    # Keep MPS in fp32 for correctness; it is slower but stable for atlas bases.
    dtype = torch.float32 if torch.backends.mps.is_available() else torch.float32
    if profile["class"] == "sdxl":
        from diffusers import ControlNetModel, StableDiffusionXLControlNetPipeline

        controlnet = ControlNetModel.from_pretrained(
            profile["controlnet"],
            torch_dtype=dtype,
            use_safetensors=True,
        )
        pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
            profile["base"],
            controlnet=controlnet,
            torch_dtype=dtype,
            use_safetensors=True,
        )
    else:
        from diffusers import ControlNetModel, StableDiffusionControlNetPipeline

        controlnet = ControlNetModel.from_pretrained(
            profile["controlnet"],
            torch_dtype=dtype,
            use_safetensors=True,
        )
        pipe = StableDiffusionControlNetPipeline.from_pretrained(
            profile["base"],
            controlnet=controlnet,
            torch_dtype=dtype,
            safety_checker=None,
            use_safetensors=True,
        )
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    pipe.to(device)
    pipe.enable_attention_slicing()
    return pipe, profile, device


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=sorted(PROFILES), default="sdxl-canny")
    ap.add_argument("--bases", nargs="+", help="base names to generate; default: all manifest items")
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--max-side", type=int, default=1344)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    manifest = load_manifest()
    wanted = set(args.bases or [item["base"] for item in manifest["items"]])
    items = [item for item in manifest["items"] if item["base"] in wanted]
    missing = wanted - {item["base"] for item in items}
    if missing:
        raise SystemExit(f"unknown bases: {sorted(missing)}")

    (ROOT / "generated").mkdir(exist_ok=True)
    torch.manual_seed(args.seed)
    pipe, profile, device = load_pipe(args.profile)
    steps = args.steps or profile["steps"]

    for item in items:
        base = item["base"]
        w, h = choose_size(item, args.max_side)
        control = Image.open(ROOT / item["control_png"]).convert("RGB").resize((w, h), Image.LANCZOS)
        subject = SHORT_SUBJECTS.get(base, item["prompt"])
        prompt = subject + STYLE_SUFFIX
        negative_prompt = NEGATIVE_PROMPT + EXTRA_NEGATIVE.get(base, "")
        print(f"GENERATE {base} {w}x{h} profile={args.profile} device={device}", flush=True)
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=control,
            width=w,
            height=h,
            num_inference_steps=steps,
            guidance_scale=profile["guidance"],
            controlnet_conditioning_scale=profile["control_scale"],
        ).images[0]
        out = ROOT / item["generated_png"]
        result.save(out)
        print(f"WROTE {out}", flush=True)


if __name__ == "__main__":
    main()
