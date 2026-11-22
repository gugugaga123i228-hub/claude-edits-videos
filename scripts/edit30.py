# Clean beat edit: hard cuts, static framing, slow push-in, white flashes,
# strobe on build, zoom punch on accents. No spins/shake/glitch.
# usage: python3 edit30.py cfg.json out.mp4 [preview]
import sys, json, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

CFG = json.load(open(sys.argv[1])); OUT = sys.argv[2]
PREVIEW = len(sys.argv) > 3 and sys.argv[3] == 'preview'
W, H, FPS = 1080, 1920, 30
DUR = CFG['dur']; N = int(round(DUR * FPS))
A0, B, NB = CFG.get('a0',0), CFG.get('b',0.5), CFG.get('nb',0)
def T(k): return A0 + B * k
FIN = T(NB)
FB = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
FM = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
SF = CFG.get('sf', 30)
cap = cv2.VideoCapture(CFG['src'])
LB = CFG.get('lb', 0)

# clips: intro [[st,cx],..] spread evenly over [0,A0]; raw [[k,nb,st,cx,(speed)]]
CL = []
iq = A0 / max(1, len(CFG.get('intro', [])))
for j, it in enumerate(CFG.get('intro', [])):
    CL.append(dict(t0=j*iq, t1=(j+1)*iq, st=it[0], cx=it[1], sp=it[2] if len(it) > 2 else 1.0, intro=True))
for r in CFG.get('raw', []):
    k, nb, st, cx = r[:4]
    CL.append(dict(t0=T(k), t1=T(k+nb), st=st, cx=cx, sp=r[4] if len(r) > 4 else 1.0, intro=False, k=k))
if 'cuts' in CFG:
    CL = []
    for t0, t1, st, cx, sp, acc, fl in CFG['cuts']:
        CL.append(dict(t0=t0, t1=t1, st=st, cx=cx, sp=sp, intro=not fl, k=('A' if acc else None)))
    FIN = CL[-1]['t1']
for i, c in enumerate(CL): c['i'] = i
ACC = set(CFG.get('accents', [])) | {'A'}  # beat indices with zoom punch

def crop(f, cx):
    if LB:
        hh = f.shape[0]; f = f[int(hh*LB):int(hh*(1-LB))]
    h, w = f.shape[:2]; cw = h*9/16
    x = min(max(cx*w, cw/2), w-cw/2); x0 = int(round(x-cw/2))
    return f[:, x0:x0+int(round(cw))]

cache = {}
def frames(c):
    if c['i'] in cache: return cache[c['i']]
    cache.clear()
    n = int((c['t1']-c['t0'])*c['sp']*SF) + 4
    cap.set(cv2.CAP_PROP_POS_MSEC, c['st']*1000); fr = []
    for _ in range(n):
        ok, f = cap.read()
        if not ok: break
        fr.append(crop(f, c['cx']))
    if not fr: fr = [np.zeros((1080, 608, 3), np.uint8)]
    cache[c['i']] = fr; return fr

LUT = None
def grade(a):
    global LUT
    if LUT is None:
        x = np.arange(256)/255.0
        s = x + CFG.get('con', 0.18)*(x - 0.5)*(1 - abs(2*x - 1))*2   # S-curve
        LUT = np.clip(s*255, 0, 255).astype(np.uint8)
    a = cv2.LUT(a, LUT)
    hsv = cv2.cvtColor(a, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1]*CFG.get('sat', 1.1), 0, 255)
    a = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    tint = CFG.get('tint')
    if tint: a = np.clip(a.astype(np.float32)*0.92 + np.array(tint[::-1], np.float32)*0.08, 0, 255).astype(np.uint8)
    return a

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.35*(((xx-W/2)/(W/2))**2 + ((yy-H/2)/(H/2))**2)/2)[:, :, None]

def scale(img, z):
    if abs(z-1) < 1e-3: return img
    M = np.float32([[z, 0, W/2*(1-z)], [0, z, H/2*(1-z)]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def card(t):
    g = np.zeros((H, W, 3), np.uint8)
    c1 = np.array(CFG.get('card1', [20, 10, 30])); c2 = np.array(CFG.get('card2', [70, 20, 110]))
    k = np.linspace(0, 1, H)[:, None, None]; g[:] = (c1*(1-k) + c2*k).astype(np.uint8)
    im = Image.fromarray(g); d = ImageDraw.Draw(im)
    a = min(1, max(0, (t-FIN)/0.25))
    def txt(s, y, sz, font):
        f = ImageFont.truetype(font, sz); w = d.textlength(s, font=f)
        d.text(((W-w)/2, y), s, font=f, fill=(int(255*a),)*3)
    txt('ИИ-ЭДИТЫ', 840, 150, FB); txt('@claude.edits2', 1030, 70, FM)
    return np.asarray(im)[:, :, ::-1].copy()

def cut_idx(t):
    for j, c in enumerate(CL):
        if t < c['t1'] - 1e-6: return j
    return len(CL)-1

STROBE = CFG.get('strobe', [])  # list of [t_start, t_end]
def render(i):
    t = i/FPS
    if t >= FIN:
        a = card(t)
    else:
        c = CL[cut_idx(t)]; lt = t - c['t0']; fr = frames(c)
        idx = min(len(fr)-1, int(lt*c['sp']*SF))
        img = cv2.resize(fr[idx], (W, H), interpolation=cv2.INTER_CUBIC)
        bl = cv2.GaussianBlur(img, (0, 0), 2.2); img = cv2.addWeighted(img, 1.45, bl, -0.45, 0)
        dur = c['t1'] - c['t0']
        z = 1.03 + 0.05*min(1, lt/max(dur, 0.5))            # slow push-in
        if not c['intro'] and c.get('k') in ACC:
            z += 0.10*math.exp(-lt/0.12)                     # punch
        img = scale(img, z)
        a = grade(img).astype(np.float32)*CFG.get('gain', 1.0)
        # white flash after cuts in the drop section
        if not c['intro'] and lt < 0.15 and CFG.get('flash', True):
            fa = (1 - lt/0.15)**2 * (0.85 if c.get('k') in ACC or c.get('k') == 0 else 0.45)
            a = a*(1-fa) + 255*fa
        for s0, s1 in STROBE:
            if s0 <= t < s1:
                ph = int((t - s0)*FPS) % 4
                a = a*(0.25 if ph < 2 else 1.15)
        a = a*VIG
    a = np.asarray(a, np.float32)
    a += np.random.RandomState(i).randn(H, W, 1).astype(np.float32)*2.5
    a = np.clip(a, 0, 255).astype(np.uint8)
    f = min(1, (DUR-t)/0.4)
    if f < 1: a = (a*max(0, f)).astype(np.uint8)
    return a

if PREVIEW:
    times = [c['t0']+0.4*(c['t1']-c['t0']) for c in CL] + [FIN+0.8]
    tiles = [cv2.resize(render(int(x*FPS)), (162, 288)) for x in times]
    cols = 10; rows = (len(tiles)+cols-1)//cols
    sh = np.zeros((rows*288, cols*162, 3), np.uint8)
    for n, tl in enumerate(tiles):
        r, cc = divmod(n, cols); sh[r*288:(r+1)*288, cc*162:(cc+1)*162] = tl
        cv2.putText(sh, str(n), (cc*162+4, r*288+18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
    cv2.imwrite(OUT, sh); sys.exit()

FC = f"[1:a]atrim={CFG['s0']}:{CFG['s0']+DUR},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.05,afade=t=out:st={DUR-0.7}:d=0.7[aout]"
cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
       '-i', CFG['aud'], '-filter_complex', FC, '-map', '0:v', '-map', '[aout]', '-t', str(DUR),
       '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for i in range(N): p.stdin.write(render(i).tobytes())
p.stdin.close(); p.wait()
