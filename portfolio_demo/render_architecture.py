#!/usr/bin/env python3
"""Render the commerce stack diagram with real technology logos.

Uses SVG brand icons from the Devicon/Simple Icons repositories where available,
and creates a visual fallback if a logo resource is unavailable.
"""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
import math
import requests
import cairosvg
from PIL import Image, ImageDraw, ImageFont

OUT = Path("demo-output")
OUT.mkdir(exist_ok=True)
W,H = 1540, 920
WHITE="#ffffff"; INK="#18263a"; SUB="#576677"; LINE="#8b98a8"
canvas=Image.new("RGB",(W,H),"#fcfdff")
d=ImageDraw.Draw(canvas)

def font(size,bold=False):
    paths=[
      "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
      "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
      if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

FH=font(27,True); FM=font(22,True); FS=font(19); FX=font(17)
def textcenter(x,y,s,f=FM,color=INK):
    b=d.textbbox((0,0),s,font=f)
    d.text((int(x-(b[2]-b[0])/2),int(y-(b[3]-b[1])/2-b[1])),s,font=f,fill=color)
def card(box,fill=WHITE,stroke="#dae3ed",radius=22,width=2):
    d.rounded_rectangle(box,fill=fill,outline=stroke,width=width,radius=radius)
def arrow(x1,y1,x2,y2,color=LINE, width=3, twoway=False):
    d.line((x1,y1,x2,y2),fill=color,width=width)
    def tip(a,b,c,e):
      angle=math.atan2(e-b,c-a)
      L=13;ang=.5
      p1=(c-L*math.cos(angle-ang),e-L*math.sin(angle-ang))
      p2=(c-L*math.cos(angle+ang),e-L*math.sin(angle+ang))
      d.polygon([(c,e),p1,p2],fill=color)
    tip(x1,y1,x2,y2)
    if twoway: tip(x2,y2,x1,y1)

def rawurl(org,path):
    return f"https://raw.githubusercontent.com/{org}/master/{path}"

ICONS={
 "next":("https://raw.githubusercontent.com/devicons/devicon/master/icons/nextjs/nextjs-original.svg",None),
 "ts":("https://raw.githubusercontent.com/devicons/devicon/master/icons/typescript/typescript-original.svg",None),
 "prisma":("https://raw.githubusercontent.com/devicons/devicon/master/icons/prisma/prisma-original.svg",None),
 "vitest":("https://raw.githubusercontent.com/devicons/devicon/master/icons/vitest/vitest-original.svg",None),
 "docker":("https://raw.githubusercontent.com/devicons/devicon/master/icons/docker/docker-original.svg",None),
 "pg":("https://raw.githubusercontent.com/devicons/devicon/master/icons/postgresql/postgresql-original.svg",None),
 "github":("https://raw.githubusercontent.com/devicons/devicon/master/icons/github/github-original.svg",None),
 "ec2":("https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/main/dist/Compute/EC2.png",None),
 "s3":("https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/main/dist/Storage/SimpleStorageService.png",None),
 "toss":("https://static.toss.im/icons/svg/logo-payments-short-blue.svg",None),
}
available={}
icons={}
for key,(url,tint) in ICONS.items():
    try:
        r=requests.get(url,timeout=18,headers={"User-Agent":"portfolio-graphic/1.0"})
        r.raise_for_status()
        if r.content[:8] == b"\x89PNG\r\n\x1a\n":
            im=Image.open(BytesIO(r.content)).convert("RGBA")
            im.thumbnail((160,160),Image.Resampling.LANCZOS)
            square=Image.new("RGBA",(160,160),(0,0,0,0))
            square.paste(im,((160-im.width)//2,(160-im.height)//2),im)
            im=square
        else:
            png=cairosvg.svg2png(bytestring=r.content,output_width=160,output_height=160)
            im=Image.open(BytesIO(png)).convert("RGBA")
        if tint:
            mask=im.getchannel("A")
            color=Image.new("RGBA",im.size,tint)
            color.putalpha(mask)
            im=color
        icons[key]=im
        available[key]=r.status_code
    except Exception as e:
        available[key]=str(e)[:80]
        # Distinct colored box containing initial(s), not a fake brand mark.
        colors={"ec2":"#f18a36","s3":"#c9504b","toss":"#348bef",
                "next":"#101010","ts":"#2473d4","prisma":"#1c3651",
                "vitest":"#a9bd38","docker":"#2397ce","pg":"#30658a","github":"#232c3a"}
        im=Image.new("RGBA",(160,160),(0,0,0,0))
        idr=ImageDraw.Draw(im)
        idr.rounded_rectangle((8,8,152,152),radius=25,fill=colors[key])
        prefix={"ec2":"EC2","s3":"S3","toss":"T","next":"N",
                "ts":"TS","prisma":"P","vitest":"V","docker":"D",
                "pg":"PG","github":"GH"}[key]
        ff=font(57 if len(prefix)<3 else 39,True)
        bb=idr.textbbox((0,0),prefix,font=ff)
        idr.text(((160-(bb[2]-bb[0]))/2,(160-(bb[3]-bb[1]))/2-bb[1]),prefix,font=ff,fill="white")
        icons[key]=im
def icon(key,cx,cy,size=70):
    im=icons[key].resize((size,size),Image.Resampling.LANCZOS)
    canvas.paste(im,(int(cx-size/2),int(cy-size/2)),im)

# Main infrastructure envelope and container
card((325,84,1002,682),fill="#fffdf9",stroke="#efa968",radius=30,width=3)
icon("ec2",538,122,56)
d.text((578,107),"AWS EC2",font=FH,fill="#a85723")
card((385,192,943,630),fill="#f5faff",stroke="#85b5df",radius=25,width=3)
icon("docker",600,237,56)
d.text((635,223),"Docker",font=FM,fill="#295974")

# Next + TypeScript + Prisma + Vitest inside backend
for (x,y,key,title,subtitle) in [
    (485,320,"next","Next.js","API Server"),
    (805,320,"ts","TypeScript","Application Logic"),
    (485,498,"prisma","Prisma","ORM"),
    (805,498,"vitest","Vitest","Testing"),
]:
    card((x-117,y-42,x+117,y+112),stroke="#e1eaf2",radius=16)
    icon(key,x,y+2,66)
    textcenter(x,y+62,title,FM)
    textcenter(x,y+94,subtitle,FX,SUB)

# Client
card((38,270,266,518),fill="#f9fbfd",stroke="#cbd7e6")
icon("next",152,345,87)
textcenter(152,421,"Next.js",FH)
textcenter(152,461,"Web / Client",FS,SUB)

# External services
card((1080,122,1492,330),fill="#fffbfb",stroke="#f0d5d5")
icon("s3",1286,180,83)
textcenter(1286,247,"Amazon S3",FH)
textcenter(1286,283,"Image Storage",FS,SUB)
card((1080,382,1492,608),fill="#f8fbff",stroke="#cadfee")
icon("toss",1286,445,86)
textcenter(1286,517,"TossPayments",FH)
textcenter(1286,561,"Payment API",FS,SUB)
card((1080,700,1492,857),fill="#fafbfc",stroke="#d1d9e3")
icon("github",1165,780,85)
d.text((1230,749),"GitHub",font=FH,fill=INK)
d.text((1230,792),"Source Control",font=FS,fill=SUB)

# PostgreSQL below EC2 as database; one true DBMS, no MySQL.
card((385,740,943,858),fill="#f9fcff",stroke="#aec4da")
icon("pg",535,797,80)
d.text((615,769),"PostgreSQL",font=FH,fill=INK)
d.text((615,813),"Order · Payment · Refund",font=FS,fill=SUB)

# Connections
arrow(266,398,325,398)
textcenter(295,367,"HTTPS",FX,SUB)
arrow(1002,245,1080,245,twoway=True)
textcenter(1040,217,"Images",FX,SUB)
arrow(1002,492,1080,492,twoway=True)
textcenter(1041,465,"Payment",FX,SUB)
arrow(665,682,665,740,twoway=True)
textcenter(777,710,"Read / Write",FX,SUB)


out=OUT/"commerce_architecture_logos.png"
canvas.save(out,optimize=True)
print("Architecture saved:",out,"bytes:",out.stat().st_size)
print("LOGO FETCH STATUS:",available)
