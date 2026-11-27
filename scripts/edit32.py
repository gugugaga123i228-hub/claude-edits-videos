# edit31: "velocity" edit engine.
#  - per-clip speed ramp (fast -> slow on the hit -> fast), frame-blended
#  - zoom-blur transitions across every cut (no white flashes, no spins)
#  - small camera shake + bass punch on accent beats
#  - face-tracked crop (cx per source time from a scan), cinematic grade + bloom
# usage: python3 edit31.py cfg.json out.mp4 [preview]
import sys, json, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
CFG = json.load(open(sys.argv[1])); OUT = sys.argv[2]; PREVIEW = len(sys.argv) > 3
W, H = 1080, 1920; FPS = CFG.get('fps', 30); DUR = CFG['dur']; N = int(round(DUR*FPS))
FB = '/usr/share/fonts/opentype/inter/Inter-Black.otf'; FM = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
SRCS = CFG['srcs']           # [[path, lb, scan_json_or_null]]
CAPS = [cv2.VideoCapture(s[0]) for s in SRCS]
SFPS = [c.get(cv2.CAP_PROP_FPS) or 30 for c in CAPS]
SCANS = []
for s in SRCS:
    if len(s) > 2 and s[2]:
        d = json.load(open(s[2])); SCANS.append(d)
    else: SCANS.append(None)
CUTS = CFG['cuts']           # [t0, t1, si, st, cx, vmin, vmax, accent]
FIN = CUTS[-1][1]
TR = CFG.get('tr', 0.10)     # half-length of the zoom-blur transition

def face_cx(si, t, default):
    sc = SCANS[si]
    if not sc: return default
    fr = sc['frames']; st = sc['step']; k = t/st
    xs = []
    for j in range(int(k)-3, int(k)+4):
        if 0 <= j < len(fr) and fr[j]['fx'] is not None: xs.append(fr[j]['fx'])
    return float(np.median(xs)) if xs else default

def src_time(c, lt):
    """integrate the speed ramp: v(x) = vmin + (vmax-vmin)*|2x-1|^1.6"""
    t0, t1, si, st, cx, vmin, vmax = c[:7]
    dur = t1 - t0; x = min(max(lt/dur, 0), 1); n = 40
    xs = np.linspace(0, x, n)
    v = vmin + (vmax-vmin)*np.abs(2*xs-1)**1.6
    return st + np.trapezoid(v, xs)*dur

cache = {}
def frames_for(i):
    if i in cache: return cache[i]
    if len(cache) > 3: cache.pop(next(iter(cache)))
    c = CUTS[i]; si = c[2]; cap = CAPS[si]; sf = SFPS[si]; lb = SRCS[si][1]
    a = src_time(c, -TR*2) if False else c[3] - TR*2
    b = src_time(c, (c[1]-c[0]) + TR*2) + 0.1
    cap.set(cv2.CAP_PROP_POS_MSEC, max(0, a)*1000); fr = []
    for _ in range(int((b-max(0, a))*sf)+2):
        ok, f = cap.read()
        if not ok: break
        if lb: hh = f.shape[0]; f = f[int(hh*lb):int(hh*(1-lb))]
        fr.append(f)
    if not fr: fr = [np.zeros((1080, 1920, 3), np.uint8)]
    cache[i] = (max(0, a), sf, fr); return cache[i]

def sample(i, ts):
    a, sf, fr = frames_for(i)
    x = (ts - a)*sf; j = int(math.floor(x)); u = x - j
    j = min(max(j, 0), len(fr)-1); k = min(j+1, len(fr)-1)
    f = fr[j] if u < 0.15 or j == k else cv2.addWeighted(fr[j], 1-u, fr[k], u, 0)
    return f

_cxs = {}
def crop(i, f, ts):
    c = CUTS[i]; si = c[2]; h, w = f.shape[:2]; cw = h*9/16
    key = (i, round(ts, 1))
    cx = face_cx(si, ts, c[4]) if SCANS[si] else c[4]
    # smooth: blend with clip's base cx
    cx = 0.6*cx + 0.4*c[4]
    x = min(max(cx*w, cw/2), w-cw/2); x0 = int(round(x-cw/2))
    g = f[:, x0:x0+int(round(cw))]
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_CUBIC)
    bl = cv2.GaussianBlur(g, (0, 0), 2.0); return cv2.addWeighted(g, 1.5, bl, -0.5, 0)

def zoom(img, z, dx=0, dy=0, rot=0):
    M = cv2.getRotationMatrix2D((W/2, H/2), rot, z); M[0, 2] += dx; M[1, 2] += dy
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def zoom_blur(img, z0, strength, n=6):
    if strength < 0.01: return zoom(img, z0)
    acc = np.zeros_like(img, np.float32)
    for k in range(n):
        acc += zoom(img, z0*(1 + strength*k/(n-1))).astype(np.float32)
    return (acc/n).astype(np.uint8)

LUT = None
def grade(a):
    global LUT
    if LUT is None:
        x = np.arange(256)/255.0; s = x + 0.22*(x-0.5)*(1-abs(2*x-1))*2
        LUT = np.clip(s*255, 0, 255).astype(np.uint8)
    if CFG.get('gain', 1.0) != 1.0: a = cv2.convertScaleAbs(a, alpha=CFG['gain'], beta=CFG.get('lift', 0))
    a = cv2.LUT(a, LUT).astype(np.float32)
    # teal shadows / warm highlights
    lum = a.mean(2, keepdims=True)/255.0
    a = a + (1-lum)*np.array([14, 6, -8]) + lum*np.array([-10, 2, 12])
    a = np.clip(a, 0, 255).astype(np.uint8)
    hsv = cv2.cvtColor(a, cv2.COLOR_BGR2HSV).astype(np.float32); hsv[:, :, 1] = np.clip(hsv[:, :, 1]*CFG.get('sat', 1.12), 0, 255)
    a = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    glow = cv2.GaussianBlur(a, (0, 0), 18)
    return cv2.addWeighted(a, 1.0, glow, CFG.get('bloom', 0.18), 0)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.38*(((xx-W/2)/(W/2))**2 + ((yy-H/2)/(H/2))**2)/2)[:, :, None]
BEATS = CFG.get('beats', [])
ACC = CFG.get('accent_beats', [])

def clip_frame(i, t):
    c = CUTS[i]; lt = t - c[0]
    ts = src_time(c, lt) if lt >= 0 else c[3] + lt*c[6]
    if lt > c[1]-c[0]: ts = src_time(c, c[1]-c[0]) + (lt-(c[1]-c[0]))*c[6]
    return crop(i, sample(i, ts), ts)

def cut_at(t):
    for i, c in enumerate(CUTS):
        if t < c[1]: return i
    return len(CUTS)-1

def card(t):
    g = np.zeros((H, W, 3), np.uint8); k = np.linspace(0, 1, H)[:, None, None]
    g[:] = (np.array([18, 8, 24])*(1-k) + np.array([90, 30, 120])*k).astype(np.uint8)
    im = Image.fromarray(g); d = ImageDraw.Draw(im); a = min(1, (t-FIN)/0.25)
    for s, y, f in (('ИИ-ЭДИТЫ', 840, ImageFont.truetype(FB, 150)), ('@claude.edits2', 1030, ImageFont.truetype(FM, 70))):
        w = d.textlength(s, font=f); d.text(((W-w)/2, y), s, font=f, fill=(int(255*a),)*3)
    return np.asarray(im)[:, :, ::-1].copy()

prev = None
def render(n):
    global prev
    t = n/FPS
    TRX = CFG.get('end_tr', 0.0)
    if TRX and t >= FIN - TRX*0.5:
        # smooth end transition: last shot blurs + pushes in, dissolves into the card, text rises in
        u = min(1.0, (t - (FIN - TRX*0.5))/TRX); e = u*u*(3-2*u)
        tl = min(t, FIN - 1.0/FPS); i = len(CUTS)-1
        base = clip_frame(i, tl); base = zoom(base, 1.03*(1 + 0.10*e))
        sig = 0.1 + 28*e; base = cv2.GaussianBlur(base, (0, 0), sig)
        base = np.clip(grade(base).astype(np.float32)*VIG, 0, 255).astype(np.uint8)
        g = np.zeros((H, W, 3), np.uint8); k = np.linspace(0, 1, H)[:, None, None]
        g[:] = (np.array([18, 8, 24])*(1-k) + np.array([90, 30, 120])*k).astype(np.uint8)
        bg = cv2.addWeighted(base, 1-e, g, e, 0)
        ta = min(1.0, max(0.0, (t - (FIN - TRX*0.5) - TRX*0.45)/(TRX*0.7))); ta = ta*ta*(3-2*ta)
        im = Image.fromarray(bg[:, :, ::-1].copy()); lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for st_, y, f in (('ИИ-ЭДИТЫ', 840, ImageFont.truetype(FB, 150)), ('@claude.edits2', 1030, ImageFont.truetype(FM, 70))):
            w = d.textlength(st_, font=f); d.text(((W-w)/2, y + 40*(1-ta)), st_, font=f, fill=(255, 255, 255, int(255*ta)))
        im = Image.alpha_composite(im.convert('RGBA'), lay).convert('RGB')
        out = np.asarray(im)[:, :, ::-1].copy()
    elif t >= FIN:
        out = card(t)
    else:
        i = cut_at(t); c = CUTS[i]; lt = t - c[0]
        img = clip_frame(i, t)
        z = 1.03
        # zoom-blur transition: end of clip zooms in & blurs, start of next comes out of blur
        tin = lt; tout = c[1] - t
        s = 0.0
        if i > 0 and tin < TR: s = (1 - tin/TR)**2*0.22; z *= 1 + s*0.6
        if i+1 < len(CUTS) and tout < TR: s = (1 - tout/TR)**2*0.22; z *= 1 + s*0.9
        # accent punch + shake
        dx = dy = rot = 0.0
        if c[7]:
            k = math.exp(-lt/CFG.get('punch_tau', 0.07)); z *= 1 + CFG.get('punch', 0.09)*k; s = max(s, CFG.get('punch_blur', 0.10)*k)
        z *= 1 + CFG.get('drift', 0.05)*min(1, lt/max(0.3, c[1]-c[0]))
        for b in ACC:
            e = t - b
            if 0 <= e < 0.35:
                k = math.exp(-e/0.09); z *= 1 + CFG.get('acc_zoom', 0.07)*k
                SH = CFG.get('shake', 0.0); dx += 22*SH*k*math.sin(e*95); dy += 16*SH*k*math.cos(e*80); rot += 0.8*SH*k*math.sin(e*70)
        img = zoom_blur(img, z, s) if s > 0.01 else zoom(img, z, dx, dy, rot)
        a = grade(img).astype(np.float32)*VIG
        out = np.clip(a, 0, 255).astype(np.uint8)
        if c[7] and lt < 0.1 and CFG.get('rgb', 0):
            sh = int(round(CFG['rgb']*(1-lt/0.1)))
            if sh > 0:
                out = out.copy(); out[:, :, 2] = np.roll(out[:, :, 2], sh, 1); out[:, :, 0] = np.roll(out[:, :, 0], -sh, 1)
        # temporal motion blur on shakes / transitions
        if prev is not None and (s > 0.02 or abs(dx) > 3) and lt > 0.045:
            out = cv2.addWeighted(out, 0.65, prev, 0.35, 0)
    prev = out
    o = out.astype(np.float32) + np.random.RandomState(n).randn(H, W, 1).astype(np.float32)*2.2
    o = np.clip(o, 0, 255).astype(np.uint8)
    f = min(1, (DUR-t)/0.4)
    return (o*max(0, f)).astype(np.uint8) if f < 1 else o

if PREVIEW:
    ts = [c[0]+0.5*(c[1]-c[0]) for c in CUTS] + [FIN+0.6]
    tl = []
    for x in ts:
        prev = None; tl.append(cv2.resize(render(int(x*FPS)), (162, 288)))
    cols = 10; rows = (len(tl)+9)//10; sh = np.zeros((rows*288, cols*162, 3), np.uint8)
    for k, x in enumerate(tl):
        r, q = divmod(k, cols); sh[r*288:(r+1)*288, q*162:(q+1)*162] = x
        cv2.putText(sh, str(k), (q*162+4, r*288+18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
    cv2.imwrite(OUT, sh); sys.exit()
SFX = CFG.get('sfx', [])
FC = f"[1:a]atrim={CFG.get('s0', 0)}:{CFG.get('s0', 0)+DUR},asetpts=PTS-STARTPTS,afade=t=out:st={DUR-0.6}:d=0.6[m]"
ins = ['-i', CFG['aud']]; mix = '[m]'
for k, (pth, t, vol) in enumerate(SFX):
    ins += ['-i', pth]; FC += f";[{k+2}:a]adelay={int(t*1000)}|{int(t*1000)},volume={vol}[s{k}]"; mix += f'[s{k}]'
FC += f";{mix}amix=inputs={len(SFX)+1}:normalize=0,alimiter=limit=0.95[a]" if SFX else ";[m]anull[a]"
cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-'] + ins + [
       '-filter_complex', FC, '-map', '0:v', '-map', '[a]', '-t', str(DUR), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19',
       '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for n in range(N): p.stdin.write(render(n).tobytes())
p.stdin.close(); p.wait()
