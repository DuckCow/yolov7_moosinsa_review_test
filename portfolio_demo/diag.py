#!/usr/bin/env python3
import json
from io import BytesIO
from pathlib import Path
import cv2, numpy as np, requests
from PIL import Image, ImageOps

BASE="https://image.uniqlo.com/UQ/ST3/WesternCommon/imagesgoods/436133"
URLS={"product":f"{BASE}/item/goods_00_436133_3x4.jpg?width=600"}
for i in range(1,14):
    URLS[f"sub{i}"]=f"{BASE}/sub/goods_436133_sub{i}_3x4.jpg?width=600"

hog=cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
cv2.setNumThreads(1)

out={}
for name,url in URLS.items():
    try:
        r=requests.get(url,timeout=20,headers={"User-Agent":"Mozilla/5.0"})
        out[name]={"status":r.status_code,"url":url}
        if r.status_code!=200:
            continue
        img=ImageOps.exif_transpose(Image.open(BytesIO(r.content))).convert("RGB")
        ow,oh=img.size
        scale=min(1.0,900/max(ow,oh))
        tw=max(64,int(round(ow*scale))); th=max(128,int(round(oh*scale)))
        small=img.resize((tw,th),Image.Resampling.LANCZOS)
        frame=cv2.cvtColor(np.asarray(small),cv2.COLOR_RGB2BGR)
        rects,margins=hog.detectMultiScale(frame,hitThreshold=-1.0,winStride=(4,4),padding=(16,16),scale=1.03,useMeanshiftGrouping=False)
        rows=[]
        for rect,margin in zip(rects,margins):
            x,y,w,h=[int(v) for v in rect]
            rows.append({
              "x":x,"y":y,"w":w,"h":h,
              "margin":float(margin),
              "h_ratio":h/th,
              "area_ratio":w*h/(tw*th)
            })
        rows.sort(key=lambda x:x["margin"],reverse=True)
        out[name].update({"size":[ow,oh],"raw_count":len(rows),"top":rows[:10]})
    except Exception as e:
        out[name]={"error":repr(e),"url":url}

Path("demo-output").mkdir(exist_ok=True)
Path("demo-output/diag.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
