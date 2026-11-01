#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from io import BytesIO

import cv2
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

OUT = Path("demo-output")
OUT.mkdir(exist_ok=True)

IMAGES = {
    "product": "https://image.uniqlo.com/UQ/ST3/WesternCommon/imagesgoods/436133/item/goods_00_436133_3x4.jpg?width=600",
    "worn": "https://image.uniqlo.com/UQ/ST3/WesternCommon/imagesgoods/436133/sub/goods_436133_sub1_3x4.jpg?width=600",
}

PERSON_DETECTOR = cv2.HOGDescriptor()
PERSON_DETECTOR.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
cv2.setNumThreads(1)

def overlap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    union = aw * ah + bw * bh - area
    return area / union if union else 0.0

def detect_fullbody_people(image: Image.Image):
    ow, oh = image.size
    scale = min(1.0, 900 / max(ow, oh))
    tw = max(64, int(round(ow * scale)))
    th = max(128, int(round(oh * scale)))
    small = image.resize((tw, th), Image.Resampling.LANCZOS)
    frame = cv2.cvtColor(np.asarray(small), cv2.COLOR_RGB2BGR)
    rects, margins = PERSON_DETECTOR.detectMultiScale(
        frame,
        hitThreshold=-1.0,
        winStride=(4, 4),
        padding=(16, 16),
        scale=1.03,
        useMeanshiftGrouping=False,
    )
    possible = []
    for rect, margin in zip(rects, margins):
        x, y, w, h = (int(n) for n in rect)
        m = float(margin)
        if m < 0.65 or h / th < 0.36 or w * h / (tw * th) < 0.035:
            continue
        bx = max(0.0, x / tw)
        by = max(0.0, y / th)
        bw = max(0.0, min(1.0 - bx, w / tw))
        bh = max(0.0, min(1.0 - by, h / th))
        possible.append({"x": bx, "y": by, "w": bw, "h": bh, "margin": m})
    possible.sort(key=lambda v: v["margin"], reverse=True)
    retained = []
    for item in possible:
        if not any(overlap(
            (item["x"], item["y"], item["w"], item["h"]),
            (prev["x"], prev["y"], prev["w"], prev["h"])
        ) > 0.35 for prev in retained):
            retained.append(item)
    return retained[:12]

def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()

def rounded(draw, xy, radius=14, fill="white", outline="#d7dbe0", width=2):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def fit_image(img, box):
    x1, y1, x2, y2 = box
    bw, bh = x2-x1, y2-y1
    tmp = ImageOps.contain(img, (bw, bh), method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (bw, bh), "white")
    canvas.paste(tmp, ((bw-tmp.width)//2, (bh-tmp.height)//2))
    return canvas

def render(name, img, boxes):
    W, H = 1200, 760
    canvas = Image.new("RGB", (W, H), "#f7f7f7")
    draw = ImageDraw.Draw(canvas)

    f_title = get_font(34, True)
    f_sub = get_font(17)
    f_h = get_font(21, True)
    f_big = get_font(34, True)
    f_body = get_font(18)
    f_small = get_font(14)

    rounded(draw, (50, 70, 690, 700), radius=16, fill="#ffffff")
    draw.text((78, 95), "INPUT", font=f_h, fill="#1c1c1c")

    img_area = (80, 140, 660, 660)
    display = fit_image(img, (0, 0, img_area[2]-img_area[0], img_area[3]-img_area[1]))
    canvas.paste(display, (img_area[0], img_area[1]))

    sx = (img_area[2]-img_area[0]) / img.width
    sy = (img_area[3]-img_area[1]) / img.height
    # contain() may add margins; reconstruct actual displayed image rect
    ratio = min((img_area[2]-img_area[0])/img.width, (img_area[3]-img_area[1])/img.height)
    dw, dh = int(img.width*ratio), int(img.height*ratio)
    ox = img_area[0] + ((img_area[2]-img_area[0])-dw)//2
    oy = img_area[1] + ((img_area[3]-img_area[1])-dh)//2
    for b in boxes:
        bx1 = ox + int(b["x"]*dw)
        by1 = oy + int(b["y"]*dh)
        bx2 = bx1 + int(b["w"]*dw)
        by2 = by1 + int(b["h"]*dh)
        draw.rectangle((bx1,by1,bx2,by2), outline="#1f6feb", width=4)

    rounded(draw, (730, 70, 1150, 700), radius=16, fill="#ffffff")
    draw.text((760, 95), "OUTPUT", font=f_h, fill="#1c1c1c")

    if boxes:
        label = "스타일 후기 후보"
        reason = "전신 인물 후보가 검출되었습니다."
        code = "STYLE_CANDIDATE"
        accent = "#1f6feb"
    else:
        label = "상품 사진 후기 후보"
        reason = "전신 인물 후보가 검출되지 않았습니다."
        code = "PRODUCT_CANDIDATE"
        accent = "#2f6f4e"

    draw.rounded_rectangle((760, 165, 1120, 255), radius=12, fill="#f5f8fb", outline=accent, width=3)
    draw.text((790, 186), label, font=f_big, fill="#111111")

    draw.text((760, 305), reason, font=f_body, fill="#333333")
    draw.text((760, 350), f"검출 인원: {len(boxes)}", font=f_body, fill="#333333")
    draw.line((760, 425, 1120, 425), fill="#dddddd", width=2)

    out = OUT / f"{name}_result.png"
    canvas.save(out)
    return {
        "input": str(OUT / f"{name}_input.jpg"),
        "screenshot": str(out),
        "label": label,
        "detected_people": len(boxes),
        "boxes": [
            {k: round(v, 5) if isinstance(v, float) else v for k,v in b.items()}
            for b in boxes
        ],
    }

def download_image(name, url):
    resp = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content))
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.save(OUT / f"{name}_input.jpg", quality=95)
    return img

def main():
    results = {}
    for name, url in IMAGES.items():
        img = download_image(name, url)
        boxes = detect_fullbody_people(img)
        results[name] = render(name, img, boxes)
        results[name]["url"] = url
    (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
