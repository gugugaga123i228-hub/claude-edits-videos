# Original cartoon characters for the "Гоша vs Саня" sketch, drawn with PIL at 2x and cached.
from PIL import Image, ImageDraw, ImageFilter
import math

SW, SH = 1040, 2000          # sprite canvas (2x)
OL = (20, 18, 22)            # outline colour
LW = 10                      # outline width at 2x

def E(d, box, fill, w=LW):
    d.ellipse(box, fill=fill, outline=OL, width=w)

def R(d, box, fill, r=40, w=LW):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=OL, width=w)

def redmi(d, cx, cy, s=1.0):
    w, h = 150*s, 290*s
    R(d, (cx-w/2, cy-h/2, cx+w/2, cy+h/2), (55, 58, 66), r=int(22*s))
    d.rounded_rectangle((cx-w/2+12*s, cy-h/2+22*s, cx+w/2-12*s, cy+h/2-22*s), radius=int(8*s), fill=(40, 150, 230))
    # cracks
    for a, b in [((-0.3, -0.35), (0.1, 0.05)), ((0.1, 0.05), (0.35, -0.2)), ((0.1, 0.05), (-0.2, 0.4)), ((0.1, 0.05), (0.3, 0.35))]:
        d.line((cx+a[0]*w, cy+a[1]*h, cx+b[0]*w, cy+b[1]*h), fill=(235, 245, 255), width=int(5*s))
    # tape
    d.polygon([(cx-w/2-8*s, cy+h*0.15), (cx+w/2+8*s, cy+h*0.05), (cx+w/2+8*s, cy+h*0.15), (cx-w/2-8*s, cy+h*0.25)], fill=(240, 200, 60), outline=OL)

def iphone_duo(d, cx, cy, s=1.0):
    w, h = 140*s, 280*s; g = 6*s
    for k in (-1, 1):
        x = cx + k*(w/2 + g/2)
        R(d, (x-w/2, cy-h/2, x+w/2, cy+h/2), (215, 220, 228), r=int(30*s))
        d.rounded_rectangle((x-w/2+10*s, cy-h/2+12*s, x+w/2-10*s, cy+h/2-12*s), radius=int(22*s), fill=(25, 25, 35))
        d.rounded_rectangle((x-28*s, cy-h/2+20*s, x+28*s, cy-h/2+38*s), radius=int(9*s), fill=(5, 5, 8))
    # glue / duct tape across both
    d.rectangle((cx-w-g, cy-14*s, cx+w+g, cy+14*s), fill=(150, 150, 160), outline=OL, width=int(5*s))

def face(d, cx, cy, who, mouth, blink, expr, look):
    # eyes
    if who == 'G':
        for ex in (cx-95, cx+95):
            E(d, (ex-72, cy-90, ex+72, cy+80), (255, 255, 255))
            if blink:
                d.chord((ex-72, cy-90, ex+72, cy+80), 180, 360, fill=(240, 196, 150), outline=OL, width=LW)
                d.line((ex-72, cy-5, ex+72, cy-5), fill=OL, width=LW)
            else:
                px = ex + 26*look; py = cy - 2
                d.ellipse((px-30, py-30, px+30, py+30), fill=OL)
                d.ellipse((px-14, py-22, px+2, py-6), fill=(255, 255, 255))
        # brows
        if expr == 'angry':
            d.line((cx-170, cy-130, cx-40, cy-95), fill=OL, width=22); d.line((cx+170, cy-130, cx+40, cy-95), fill=OL, width=22)
        elif expr == 'smug':
            d.line((cx-165, cy-120, cx-35, cy-130), fill=OL, width=20); d.line((cx+35, cy-150, cx+165, cy-120), fill=OL, width=20)
        else:
            d.arc((cx-175, cy-170, cx-35, cy-90), 200, 330, fill=OL, width=20); d.arc((cx+35, cy-170, cx+175, cy-90), 210, 340, fill=OL, width=20)
        # nose
        d.ellipse((cx-28+10*look, cy+70, cx+30+10*look, cy+120), fill=(235, 170, 130), outline=OL, width=8)
        my = cy + 190
    else:
        if expr == 'dead':
            for ex in (cx-95, cx+95):
                d.line((ex-50, cy-50, ex+50, cy+50), fill=OL, width=22); d.line((ex-50, cy+50, ex+50, cy-50), fill=OL, width=22)
            d.ellipse((cx-26, cy+70, cx+28, cy+118), fill=(232, 178, 140), outline=OL, width=8)
            my = cy + 190
            d.ellipse((cx-70, my-25, cx+70, my+35), fill=(120, 25, 35), outline=OL, width=LW)
            d.rounded_rectangle((cx+5, my+10, cx+60, my+110), radius=25, fill=(230, 100, 110), outline=OL, width=8)
            return
        # sunglasses
        for ex in (cx-95, cx+95):
            d.rounded_rectangle((ex-82, cy-60, ex+82, cy+55), radius=34, fill=(15, 15, 22), outline=OL, width=LW)
            d.line((ex-45, cy-35, ex-10, cy-35), fill=(120, 130, 160), width=10)
        d.line((cx-13, cy-30, cx+13, cy-30), fill=OL, width=14)
        if expr == 'angry':
            d.line((cx-170, cy-110, cx-40, cy-80), fill=(150, 120, 40), width=20); d.line((cx+170, cy-110, cx+40, cy-80), fill=(150, 120, 40), width=20)
        elif expr == 'smug':
            d.line((cx-165, cy-95, cx-35, cy-100), fill=(150, 120, 40), width=18); d.line((cx+35, cy-125, cx+165, cy-95), fill=(150, 120, 40), width=18)
        d.ellipse((cx-26+8*look, cy+70, cx+28+8*look, cy+118), fill=(232, 178, 140), outline=OL, width=8)
        my = cy + 185
    # mouth
    mx = cx + 10*look
    if mouth == 0:
        if expr == 'smug':
            d.arc((mx-70, my-40, mx+70, my+30), 20, 160, fill=OL, width=12)
        elif expr == 'angry':
            d.line((mx-55, my, mx+55, my-6), fill=OL, width=12)
        else:
            d.arc((mx-55, my-30, mx+55, my+20), 30, 150, fill=OL, width=12)
    else:
        hh = [0, 28, 55, 85][mouth]; ww = [0, 60, 75, 90][mouth]
        d.ellipse((mx-ww, my-hh/2-10, mx+ww, my+hh), fill=(120, 25, 35), outline=OL, width=LW)
        if mouth >= 2:
            d.chord((mx-ww*0.6, my+hh*0.25, mx+ww*0.6, my+hh*0.95), 180, 360, fill=(230, 100, 110))
            d.rectangle((mx-ww*0.55, my-hh/2-4, mx+ww*0.55, my-hh/2+12), fill=(255, 255, 255))

def draw(who, mouth=0, blink=0, expr='normal', look=1, arm='hold'):
    im = Image.new('RGBA', (SW, SH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = SW//2
    if who == 'G':
        skin = (247, 208, 168); top = (46, 150, 80); stripe = (245, 245, 245); pants = (45, 50, 70); shoe = (240, 240, 240)
    else:
        skin = (240, 200, 165); top = (32, 32, 40); stripe = None; pants = (200, 180, 140); shoe = (250, 250, 250)
    # legs
    for k in (-1, 1):
        R(d, (cx+k*95-62, 1330, cx+k*95+62, 1880), pants, r=30)
        R(d, (cx+k*110-95, 1850, cx+k*110+95, 1960), shoe, r=45)
    # torso
    R(d, (cx-215, 760, cx+215, 1400), top, r=110)
    if stripe:
        d.line((cx, 790, cx, 1380), fill=(30, 110, 60), width=10)   # zipper
        d.rounded_rectangle((cx-40, 760, cx+40, 840), radius=20, fill=top, outline=OL, width=8)
    else:
        # hood + gold chain
        d.ellipse((cx-150, 720, cx+150, 860), fill=(45, 45, 55), outline=OL, width=LW)
        for k in range(15):
            a = math.pi*(0.15 + 0.7*k/14); x = cx + 135*math.cos(a); y = 820 + 160*math.sin(a)
            d.ellipse((x-14, y-14, x+14, y+14), fill=(250, 200, 50), outline=(120, 90, 10), width=4)
    # neck + head
    R(d, (cx-55, 680, cx+55, 800), skin, r=20)
    hy = 430
    if who == 'G':
        for ex in (cx-250, cx+250):
            E(d, (ex-62, hy-40, ex+62, hy+120), skin)
    E(d, (cx-260, hy-300, cx+260, hy+290), skin)
    # hair
    if who == 'G':
        d.chord((cx-262, hy-302, cx+262, hy+290), 192, 348, fill=(110, 70, 40), outline=OL, width=LW)
        for k in range(9):
            x = cx - 200 + k*50
            d.polygon([(x-30, hy-200 + abs(k-4)*14), (x, hy-300 + abs(k-4)*22 - 20), (x+30, hy-200 + abs(k-4)*14)], fill=(110, 70, 40), outline=OL)
    else:
        d.chord((cx-262, hy-302, cx+262, hy+290), 185, 355, fill=(245, 215, 95), outline=OL, width=LW)
        d.ellipse((cx-290, hy-380, cx+250, hy-120), fill=(245, 215, 95), outline=OL, width=LW)
        d.chord((cx-262, hy-302, cx+262, hy+290), 195, 345, fill=(245, 215, 95))
        for k in range(4):
            d.arc((cx-250+k*60, hy-360+k*10, cx+200, hy-120), 200, 300, fill=(205, 165, 50), width=9)
    face(d, cx, hy + 20, who, mouth, blink, expr, look)
    # arms + phone
    side = 1 if who == 'G' else -1          # phone hand faces the other character
    if arm in ('throw', 'none'):
        R(d, (cx-side*215-70, 820, cx-side*215+40, 1300), top, r=50)
        E(d, (cx-side*215-75, 1250, cx-side*215+45, 1370), skin)
        if arm == 'throw':
            sx, sy = cx + side*190, 850; px, py = cx + side*330, 420
        else:
            sx, sy = cx + side*190, 850; px, py = cx + side*240, 1300
        ang = math.atan2(py-sy, px-sx); nx, ny = -math.sin(ang)*55, math.cos(ang)*55
        d.polygon([(sx+nx, sy+ny), (px+nx, py+ny), (px-nx, py-ny), (sx-nx, sy-ny)], fill=top, outline=OL)
        E(d, (px-60, py-50, px+60, py+60), skin)
        return im
    if arm == 'show':
        px, py = cx + side*300, 820
    else:
        px, py = cx + side*150, 1080
    # far arm hanging
    R(d, (cx-side*215-70, 820, cx-side*215+40, 1300), top, r=50)
    E(d, (cx-side*215-75, 1250, cx-side*215+45, 1370), skin)
    # phone arm (polygon from shoulder to hand)
    sx, sy = cx + side*190, 850
    ang = math.atan2(py-sy, px-sx); nx, ny = -math.sin(ang)*55, math.cos(ang)*55
    d.polygon([(sx+nx, sy+ny), (px+nx, py+ny), (px-nx, py-ny), (sx-nx, sy-ny)], fill=top, outline=OL)
    if who == 'G': redmi(d, px, py - 40, 1.0)
    else: iphone_duo(d, px, py - 40, 1.0)
    E(d, (px-60, py-10, px+60, py+90), skin)
    return im

_cache = {}
def sprite(who, mouth, blink, expr, look, arm, h):
    k = (who, mouth, blink, expr, look, arm, h)
    if k not in _cache:
        if len(_cache) > 400: _cache.clear()
        im = draw(who, mouth, blink, expr, look, arm)
        w = int(SW*h/SH); _cache[k] = im.resize((w, h), Image.LANCZOS)
    return _cache[k]
