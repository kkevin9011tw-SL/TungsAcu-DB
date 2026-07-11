#!/usr/bin/env python3
"""董氏奇穴底圖套皮正式管線(2026-07-03 E 方案定案)。

流程(每張底圖一次,全部穴位共用):
  線稿底圖 → 輪廓控制圖(去骨線) → flux-canny-pro 生成皮膚
  → 還原座標系 → 去背純白 → 皮膚吸附真值輪廓 → 疊真值輪廓線+骨骼層
  → QC → 正式底圖(尺寸與原底圖相同,marker JSON 全部沿用)

用法:
  python3 pipeline.py plan [底圖名]            # 檢視/建議每張的 work_box 與 FLUX bucket
  python3 pipeline.py run <底圖名> [--reuse]   # 跑單張(--reuse 沿用已生成的皮膚,不花錢)
  python3 pipeline.py points <marked.json> <底圖final.png> <輸出.png>  # 驗證後疊穴位紅點
  python3 pipeline.py verify-points <marked.json> <底圖final.png> [檢查圖.png]

需要環境變數 REPLICATE_API_TOKEN(在 ~/.zshrc)。
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).parent
BASES_DIR = HERE.parent / "who-standard-bases-20260612" / "clean-bases"
CACHE = HERE / "cache"
OUT = HERE / "output"
QC = HERE / "qc"
SCALE = 6  # clean-bases PNG = viewBox x 6

CFG = json.loads((HERE / "bases.json").read_text())
DEF = CFG["defaults"]


def cfgv(base_cfg, key):
    return base_cfg.get(key, DEF[key])


def svg_viewbox(name):
    """讀取底圖 viewBox，作為 JSON 與 PNG 座標換算的唯一真值。"""
    path = BASES_DIR / f"{name}.svg"
    text = path.read_text(errors="ignore")[:4000]
    m = re.search(r"\bviewBox\s*=\s*[\"']([^\"']+)[\"']", text)
    if not m:
        raise ValueError(f"{path}: 找不到 viewBox")
    values = [float(value) for value in re.split(r"[\s,]+", m.group(1).strip())]
    if len(values) != 4:
        raise ValueError(f"{path}: viewBox 格式無法解析: {m.group(1)!r}")
    return tuple(values)


def svg_viewbox_origin(name):
    ox, oy, _, _ = svg_viewbox(name)
    return ox, oy


# ---------- FLUX bucket 預測(輸出為 32 倍數、總像素約 1MP) ----------
def flux_buckets():
    out = []
    for w in range(320, 1600, 32):
        for h in range(320, 1600, 32):
            if 0.98e6 <= w * h <= 1.03e6:
                out.append((w, h))
    return out


def suggest_work_box(W, H, open_sides):
    """建議把底圖 pad/crop 成哪個框,使長寬比恰為某個 FLUX bucket。優先 pad 不動解剖。"""
    best = None
    for bw, bh in flux_buckets():
        r = bw / bh
        # 方案一:調寬(左右 pad 或 crop),高度不動
        w2 = H * r
        pad_w = w2 - W  # >0 = pad,<0 = crop
        ok_w = pad_w >= 0 or ("left" not in open_sides and "right" not in open_sides)
        # 方案二:調高,寬度不動
        h2 = W / r
        pad_h = h2 - H
        ok_h = pad_h >= 0 and not ({"top", "bottom"} & set(open_sides)) or pad_h >= 0 and False
        cands = []
        if ok_w:
            cands.append((abs(pad_w), "width", w2))
        if pad_h >= 0 and not ({"top", "bottom"} & set(open_sides)):
            cands.append((abs(pad_h), "height", h2))
        for cost, mode, dim in cands:
            if best is None or cost < best[0]:
                if mode == "width":
                    dx = (dim - W) / 2
                    box = [-round(dx), 0, W + round(dim - W - round(dx)), H]
                else:
                    dy = (dim - H) / 2
                    box = [0, -round(dy), W, H + round(dim - H - round(dy))]
                best = (cost, box, (bw, bh))
    return best


# ---------- 影像工具 ----------
def load_base(name):
    img = Image.open(BASES_DIR / f"{name}.png").convert("RGB")
    return img


def outline_and_bones(base_img, bc):
    g = base_img.convert("L")
    t_out, lo, hi = cfgv(bc, "outline_thresh"), cfgv(bc, "bones_lo"), cfgv(bc, "bones_hi")
    outline = g.point(lambda v: 0 if v < t_out else 255)
    bones = g.point(lambda v: v if lo <= v <= hi else 255)
    return outline, bones


def apply_work_box(img, box, fill=255):
    """box 可超出原圖(=pad 白)。回傳裁/墊後影像。"""
    x0, y0, x1, y1 = box
    canvas = Image.new(img.mode, (x1 - x0, y1 - y0), (fill,) * len(img.getbands()))
    canvas.paste(img, (-x0, -y0))
    return canvas


def open_side_seal(dark, side):
    """Return a short seal segment for one intentionally open anatomical cut edge."""
    H, W = dark.shape
    ys, xs = np.where(dark)
    if len(xs) == 0:
        return None
    band = max(80, round((H if side in ("top", "bottom") else W) * 0.18))
    if side == "top":
        y0 = int(ys.min())
        keep = ys <= min(H - 1, y0 + band)
        bxs, bys = xs[keep], ys[keep]
        if len(bxs) < 2:
            return None
        mid = (int(bxs.min()) + int(bxs.max())) / 2
        left, right = bxs <= mid, bxs > mid
        if not left.any() or not right.any():
            return None
        p1 = (int(bxs[left][np.argmin(bys[left])]), int(bys[left].min()))
        p2 = (int(bxs[right][np.argmin(bys[right])]), int(bys[right].min()))
        return p1, p2
    if side == "bottom":
        y0 = int(ys.max())
        keep = ys >= max(0, y0 - band)
        bxs, bys = xs[keep], ys[keep]
        if len(bxs) < 2:
            return None
        mid = (int(bxs.min()) + int(bxs.max())) / 2
        left, right = bxs <= mid, bxs > mid
        if not left.any() or not right.any():
            return None
        p1 = (int(bxs[left][np.argmax(bys[left])]), int(bys[left].max()))
        p2 = (int(bxs[right][np.argmax(bys[right])]), int(bys[right].max()))
        return p1, p2
    if side == "left":
        x0 = int(xs.min())
        keep = xs <= min(W - 1, x0 + band)
        bxs, bys = xs[keep], ys[keep]
        if len(bys) < 2:
            return None
        mid = (int(bys.min()) + int(bys.max())) / 2
        top, bottom = bys <= mid, bys > mid
        if not top.any() or not bottom.any():
            return None
        p1 = (int(bxs[top].min()), int(bys[top][np.argmin(bxs[top])]))
        p2 = (int(bxs[bottom].min()), int(bys[bottom][np.argmin(bxs[bottom])]))
        return p1, p2
    if side == "right":
        x0 = int(xs.max())
        keep = xs >= max(0, x0 - band)
        bxs, bys = xs[keep], ys[keep]
        if len(bys) < 2:
            return None
        mid = (int(bys.min()) + int(bys.max())) / 2
        top, bottom = bys <= mid, bys > mid
        if not top.any() or not bottom.any():
            return None
        p1 = (int(bxs[top].max()), int(bys[top][np.argmax(bxs[top])]))
        p2 = (int(bxs[bottom].max()), int(bys[bottom][np.argmax(bxs[bottom])]))
        return p1, p2
    return None


def sealed_interior(outline_full, open_sides, seal_strategy="short"):
    """回傳(interior bool array, seal 座標 dict)。outline_full 為全幅 L 圖。"""
    a = np.array(outline_full)
    dark = a < 128
    seals = {}
    thick = outline_full.filter(ImageFilter.MinFilter(3))
    m = thick.point(lambda v: 255 if v > 128 else 0)
    d = ImageDraw.Draw(m)
    W, H = m.size
    seal_mask = Image.new("1", (W, H), 0)
    sd = ImageDraw.Draw(seal_mask)
    rows = np.where(dark.any(axis=1))[0]
    cols = np.where(dark.any(axis=0))[0]
    for side in open_sides:
        if seal_strategy == "full_span":
            if side == "bottom":
                y = int(rows.max()) - 2
                pts = ((0, y), (W, y))
            elif side == "top":
                y = int(rows.min()) + 2
                pts = ((0, y), (W, y))
            elif side == "left":
                x = int(cols.min()) + 2
                pts = ((x, 0), (x, H))
            elif side == "right":
                x = int(cols.max()) - 2
                pts = ((x, 0), (x, H))
            else:
                pts = None
        else:
            pts = open_side_seal(dark, side)
        if not pts:
            continue
        d.line(pts, fill=0, width=8)
        sd.line(pts, fill=1, width=10)
        seals[side] = [list(pts[0]), list(pts[1])]
    arr = np.array(m)
    # 從所有邊界白點 floodfill(用 mark 值 128)
    mm = m.copy()
    for x in range(0, W, 40):
        for y in [0, H - 1]:
            if mm.getpixel((x, y)) == 255:
                ImageDraw.floodfill(mm, (x, y), 128)
    for y in range(0, H, 40):
        for x in [0, W - 1]:
            if mm.getpixel((x, y)) == 255:
                ImageDraw.floodfill(mm, (x, y), 128)
    interior = (np.array(mm) != 128) & ~np.array(seal_mask, dtype=bool)
    return interior, seals


def span_interior(outline_full):
    """Fallback for open line art that is not watertight.

    For each row, use the outermost dark outline pixels as left/right borders and
    fill between them. This is less anatomically selective than floodfill, but it
    recovers simple limb surfaces that are drawn as two open contour strokes.
    """
    dark = np.array(outline_full) < 128
    H, W = dark.shape
    left = np.full(H, np.nan)
    right = np.full(H, np.nan)
    for y in range(H):
        xs = np.where(dark[y])[0]
        if len(xs) < 2:
            continue
        l, r = np.percentile(xs, [2, 98])
        if r - l > 8 and r - l < W * 0.92:
            left[y], right[y] = l, r
    valid = np.where(~np.isnan(left))[0]
    if len(valid) < 2:
        return np.zeros((H, W), dtype=bool)
    ys = np.arange(H)
    left_i = np.interp(ys, valid, left[valid])
    right_i = np.interp(ys, valid, right[valid])
    mask = np.zeros((H, W), dtype=bool)
    for y in range(int(valid.min()), int(valid.max()) + 1):
        l = max(0, int(round(left_i[y])))
        r = min(W - 1, int(round(right_i[y])))
        if r - l > 8:
            mask[y, l:r + 1] = True
    im = Image.fromarray((mask * 255).astype("uint8"))
    im = im.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    return np.array(im) > 128


def source_nonwhite_interior(base_img, thresh=250):
    a = np.array(base_img.convert("RGB"))
    mask = np.any(a < thresh, axis=2)
    im = Image.fromarray((mask * 255).astype("uint8"))
    im = im.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    return np.array(im) > 128


def interior_for(base_img, outline_full, bc):
    strategy = bc.get("mask_strategy", "sealed")
    if strategy == "span":
        return span_interior(outline_full), {"strategy": "span"}
    if strategy == "source_nonwhite":
        thresh = bc.get("mask_thresh", 250)
        return source_nonwhite_interior(base_img, thresh), {"strategy": "source_nonwhite", "thresh": thresh}
    return sealed_interior(outline_full, bc["open_sides"], bc.get("seal_strategy", "short"))


def shiftf(a, dy, dx):
    out = np.zeros_like(a)
    ys, ye = max(dy, 0), a.shape[0] + min(dy, 0)
    xs, xe = max(dx, 0), a.shape[1] + min(dx, 0)
    out[ys:ye, xs:xe] = a[ys - dy:ye - dy, xs - dx:xe - dx]
    return out


def snap_fill(arr, interior, bc):
    """暖色皮膚判斷 + 3x3 位移平均迭代補到真值輪廓。回傳(filled, stats)。"""
    R, B = arr[..., 0], arr[..., 2]
    total = arr.sum(axis=2)
    have = (R - B > cfgv(bc, "fill_warm_min")) & \
           (total < cfgv(bc, "fill_sum_max")) & (total > cfgv(bc, "fill_sum_min"))
    todo0 = int((interior & ~have).sum())
    spill = int((have & ~interior).sum())
    filled = arr.copy()
    iters = 0
    for it in range(cfgv(bc, "fill_max_iters")):
        todo = interior & ~have
        if not todo.any():
            break
        acc = np.zeros_like(filled)
        cnt = np.zeros(filled.shape[:2])
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == dx == 0:
                    continue
                h = shiftf(have.astype(float), dy, dx)
                acc += shiftf(filled, dy, dx) * h[..., None]
                cnt += h
        newly = todo & (cnt > 0)
        if not newly.any():
            break
        filled[newly] = acc[newly] / cnt[newly][:, None]
        have |= newly
        iters = it + 1
    left = int((interior & ~have).sum())
    return filled, {"todo_px": todo0, "spill_px": spill, "fill_iters": iters, "unfilled_px": left}


# ---------- Replicate ----------
def replicate(base, bc, control_png):
    token = os.environ.get("REPLICATE_API_TOKEN", "")
    if not token:
        sys.exit("缺 REPLICATE_API_TOKEN(source ~/.zshrc)")
    up = subprocess.run(
        ["curl", "-s", "-X", "POST", "-H", f"Authorization: Bearer {token}",
         "-F", f"content=@{control_png}", "https://api.replicate.com/v1/files"],
        capture_output=True, text=True, check=True)
    url = json.loads(up.stdout)["urls"]["get"]
    prompt = bc.get("prompt") or cfgv(bc, "prompt_template").format(subject=bc["subject"])
    req = {"input": {"prompt": prompt, "control_image": url,
                     "guidance": cfgv(bc, "guidance"), "steps": cfgv(bc, "steps"),
                     "seed": cfgv(bc, "seed"), "output_format": "png", "safety_tolerance": 2}}
    reqf = CACHE / f"{base}_req.json"
    reqf.write_text(json.dumps(req, ensure_ascii=False))
    attempts = cfgv(bc, "replicate_attempts")
    for att in range(attempts):
        r = subprocess.run(
            ["curl", "-s", "-X", "POST", "-H", f"Authorization: Bearer {token}",
             "-H", "Content-Type: application/json", "-H", "Prefer: wait=60",
             "-d", f"@{reqf}",
             "https://api.replicate.com/v1/models/black-forest-labs/flux-canny-pro/predictions"],
            capture_output=True, text=True, check=True)
        d = json.loads(r.stdout)
        (CACHE / f"{base}_pred.json").write_text(r.stdout)
        if d.get("status") == "succeeded":
            out = CACHE / f"{base}_gen.png"
            subprocess.run(["curl", "-s", "-o", str(out), d["output"]], check=True)
            return out
        print(f"  attempt {att+1}: {d.get('status')} {d.get('detail','')}", flush=True)
        time.sleep(25)
    sys.exit(f"{base}: 生成失敗,詳見 cache/{base}_pred.json")


# ---------- 指令 ----------
def cmd_plan(only=None):
    for base, bc in CFG["bases"].items():
        if only and base != only:
            continue
        if bc.get("skip"):
            print(f"{base}: SKIP ({bc.get('note','')})")
            continue
        img = load_base(base)
        W, H = img.size
        sug = suggest_work_box(W, H, bc["open_sides"])
        wb = bc.get("work_box")
        print(f"{base}: {W}x{H} open={bc['open_sides']} "
              f"work_box={'已設 '+str(wb) if wb else '建議 '+str(sug[1])+' bucket '+str(sug[2]) if sug else '無解,需手動'}")


def cmd_run(base, reuse=False):
    bc = CFG["bases"][base]
    if bc.get("skip"):
        sys.exit(f"{base} 標記為 skip:{bc.get('note','')}")
    for p in (CACHE, OUT, QC):
        p.mkdir(exist_ok=True)
    img = load_base(base)
    W, H = img.size
    box = bc.get("work_box")
    if not box:
        sug = suggest_work_box(W, H, bc["open_sides"])
        if not sug:
            sys.exit(f"{base}: 無可用 work_box,請在 bases.json 手動設定")
        box = sug[1]
        print(f"  work_box 未設,採用建議 {box}(bucket {sug[2]})")
    outline_full, bones_full = outline_and_bones(img, bc)

    # 控制圖(去骨線,work_box 幅面)
    ctrl = apply_work_box(outline_full, box).convert("RGB")
    ctrl_png = CACHE / f"{base}_control.png"
    ctrl.save(ctrl_png)

    gen_png = CACHE / f"{base}_gen.png"
    if reuse and gen_png.exists():
        print("  --reuse:沿用既有生成圖")
    else:
        print("  呼叫 flux-canny-pro …")
        replicate(base, bc, ctrl_png)
    gen = Image.open(gen_png).convert("RGB")
    gr = gen.size[0] / gen.size[1]
    br = (box[2] - box[0]) / (box[3] - box[1])
    if abs(gr - br) / br > 0.005:
        sys.exit(
            f"{base}: 生成圖比例 {gr:.4f} 與 work_box {br:.4f} 不符; "
            "停止輸出,不可拉伸後再疊穴位。請調整 work_box 或重新生成。"
        )

    # 還原座標系
    skin_wb = gen.resize((box[2] - box[0], box[3] - box[1]), Image.LANCZOS)
    canvas = Image.new("RGB", (W, H), "white")
    canvas.paste(skin_wb, (box[0], box[1]))
    arr = np.array(canvas).astype(np.float64)

    interior, seals = interior_for(img, outline_full, bc)
    filled, stats = snap_fill(arr, interior, bc)
    filled[~interior] = 255
    out = Image.fromarray(filled.astype(np.uint8))

    # 疊真值輪廓 + 骨骼層
    a_out, a_bone = cfgv(bc, "outline_alpha"), cfgv(bc, "bone_alpha")
    soft_line = outline_full.point(lambda v: int(255 - (255 - v) * a_out) if v < 128 else 255).convert("RGB")
    faint_bone = bones_full.point(lambda v: int(255 - (255 - v) * a_bone)).convert("RGB")
    final = ImageChops.multiply(out, faint_bone)
    final = ImageChops.multiply(final, soft_line)

    final_png = OUT / f"{base}_final.png"
    final.save(final_png)

    ImageChops.multiply(final.convert("RGB"), img).save(QC / f"{base}_QC_line_over_final.png")
    stats["seals"] = seals
    (QC / f"{base}_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1))
    print(f"  完成 → {final_png}")
    print(f"  QC: 缺皮膚 {stats['todo_px']}px / 溢出 {stats['spill_px']}px / "
          f"補色 {stats['fill_iters']} 輪 / 未補 {stats['unfilled_px']}px")
    if stats["todo_px"] > cfgv(bc, "qc_todo_warn"):
        print("  ⚠ 缺皮膚像素偏多,請人工看 QC 圖,必要時換 seed 重生成")


def point_overlay_report(marked_json, final_png):
    """確認套皮 PNG 仍在 marker JSON 對應的底圖座標系中。"""
    data = json.loads(Path(marked_json).read_text())
    base_file = data.get("base_file")
    if not base_file:
        raise ValueError(f"{marked_json}: 缺少 base_file")
    base = Path(base_file).stem
    if base not in CFG["bases"]:
        raise ValueError(f"{marked_json}: 未知底圖 {base_file}")

    base_img = load_base(base)
    final_img = Image.open(final_png).convert("RGB")
    outline, _ = outline_and_bones(base_img, CFG["bases"][base])
    interior, _ = interior_for(base_img, outline, CFG["bases"][base])
    ox, oy, view_w, view_h = svg_viewbox(base)
    expected_svg_size = (round(view_w * SCALE), round(view_h * SCALE))
    errors = []
    if base_img.size != expected_svg_size:
        errors.append(
            f"底圖 {base} 的 PNG 尺寸 {base_img.size} 與 SVG viewBox x {SCALE} "
            f"預期 {expected_svg_size} 不符"
        )
    if final_img.size != base_img.size:
        errors.append(
            f"套皮圖尺寸 {final_img.size} 不等於 {base} 底圖尺寸 {base_img.size}"
        )

    # 最終圖必須仍保有原始外輪廓；否則即使尺寸相同，也可能是另一張手勢的圖。
    outline_mask = np.array(outline) < 128
    final_gray = np.array(final_img.convert("L"))
    line_match_ratio = float((final_gray[outline_mask] < 245).mean()) if outline_mask.any() else 0.0
    if line_match_ratio < 0.85:
        errors.append(f"原始外輪廓保留率僅 {line_match_ratio:.1%}，疑似不是同一張底圖或輪廓已漂移")

    points = []
    width, height = final_img.size
    for index, ann in enumerate(data.get("annotations", [])):
        if ann.get("type") != "point":
            continue
        try:
            x, y = (float(value) for value in ann["xy"])
            radius = float(ann.get("r", 8)) * SCALE * 0.15
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"第 {index} 筆 point 座標無法解析: {exc}")
            continue
        px, py = (x - ox) * SCALE, (y - oy) * SCALE
        in_canvas = 0 <= px < width and 0 <= py < height
        inside_body = False
        if in_canvas:
            ix = min(width - 1, max(0, round(px)))
            iy = min(height - 1, max(0, round(py)))
            inside_body = bool(interior[iy, ix])
        if not in_canvas:
            errors.append(f"第 {index} 筆 point ({px:.1f}, {py:.1f}) 超出成圖畫布")
        elif not inside_body:
            errors.append(f"第 {index} 筆 point ({px:.1f}, {py:.1f}) 不在 {base} 人體遮罩內")
        points.append({
            "annotation_id": ann.get("id"),
            "px": round(px, 3),
            "py": round(py, 3),
            "radius": round(radius, 3),
            "inside_body": inside_body,
        })
    if not points:
        errors.append("JSON 沒有 type: point 的穴位資料")
    return final_img, outline, points, {
        "base": base,
        "base_size": list(base_img.size),
        "final_size": list(final_img.size),
        "viewbox": [ox, oy, view_w, view_h],
        "outline_match_ratio": round(line_match_ratio, 5),
        "points": points,
        "errors": errors,
    }


def save_point_review(final_img, outline, points, out_png):
    """輸出只供人工核對的座標檢查圖，不作網站成品。"""
    review = final_img.convert("RGBA")
    outline_rgba = outline.convert("L").point(lambda value: 120 if value < 128 else 0)
    cyan = Image.new("RGBA", review.size, (0, 145, 170, 0))
    cyan.putalpha(outline_rgba)
    review.alpha_composite(cyan)
    draw = ImageDraw.Draw(review)
    for point in points:
        px, py = point["px"], point["py"]
        color = (20, 150, 80, 255) if point["inside_body"] else (220, 30, 30, 255)
        draw.line((px - 8, py, px + 8, py), fill=color, width=2)
        draw.line((px, py - 8, px, py + 8), fill=color, width=2)
    review.save(out_png)


def cmd_verify_points(marked_json, final_png, review_png=None):
    final_img, outline, points, report = point_overlay_report(marked_json, final_png)
    if review_png:
        save_point_review(final_img, outline, points, review_png)
        report["review_image"] = str(review_png)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["errors"]:
        sys.exit("穴位座標驗證失敗；未輸出網站用成圖。")


def cmd_points(marked_json, final_png, out_png):
    data = json.loads(Path(marked_json).read_text())
    img, _, points, report = point_overlay_report(marked_json, final_png)
    if report["errors"]:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.exit("穴位座標驗證失敗；未輸出網站用成圖。")
    d = ImageDraw.Draw(img)
    for point in points:
        px, py, r = point["px"], point["py"], point["radius"]
        d.ellipse([px - r - 2, py - r - 2, px + r + 2, py + r + 2], fill="white")
        d.ellipse([px - r, py - r, px + r, py + r], fill=(196, 30, 30))
    img.save(out_png)
    print(f"座標驗證通過，疊了 {len(points)} 個點 → {out_png}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == "plan":
        cmd_plan(args[1] if len(args) > 1 else None)
    elif args[0] == "run":
        cmd_run(args[1], reuse="--reuse" in args)
    elif args[0] == "points":
        cmd_points(args[1], args[2], args[3])
    elif args[0] == "verify-points":
        cmd_verify_points(args[1], args[2], args[3] if len(args) > 3 else None)
    else:
        sys.exit(__doc__)
