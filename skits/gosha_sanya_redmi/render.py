import json, math, sys, subprocess, re
import numpy as np, librosa, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from chars import sprite, redmi, iphone_duo, draw as cdraw

W, H, FPS = 1080, 1920, 30
TL = json.load(open('timeline.json')); LINES = TL['lines']; DUR = TL['dur']
PREVIEW = len(sys.argv) > 1 and sys.argv[1] == 'preview'
FB = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
SR = 44100

# ---------------- audio ----------------
src = {f: librosa.load(f, sr=SR)[0] for f in ('g.wav', 's2.wav', 'g2.wav', 'np_.wav')}
N = int((DUR+0.5)*SR); tracks = {k: np.zeros(N, np.float32) for k in 'GSN'}; fx = np.zeros(N, np.float32)
for L in LINES:
    if L['who'] == 'THROW':
        i = int(L['t0']*SR); n = int(0.45*SR); tt = np.arange(n)/SR
        wh = np.random.RandomState(1).randn(n).astype(np.float32)*np.sin(np.pi*tt/0.45)**2*0.25
        fx[i:i+n] += np.convolve(wh, np.ones(30)/30, 'same')
        j = int((L['t0']+0.45)*SR); m = int(0.5*SR); tt = np.arange(m)/SR
        bonk = 0.8*np.sin(2*np.pi*np.cumsum(700*np.exp(-tt*9)+90)/SR)*np.exp(-tt*7)
        fx[j:j+m] += bonk.astype(np.float32)
        b2 = librosa.load('/home/claude/gta/boom.mp3', sr=SR)[0]*0.6; k = min(len(b2), N-j); fx[j:j+k] += b2[:k]
        continue
    if L['who'] == 'RING':
        t = np.arange(int(1.6*SR))/SR
        env = ((t % 0.8) < 0.5).astype(np.float32)
        ring = 0.22*env*(np.sin(2*np.pi*880*t)*0.6 + np.sin(2*np.pi*1320*t)*0.4)*(np.sin(2*np.pi*12*t) > 0)
        i = int(L['t0']*SR); fx[i:i+len(ring)] += ring; continue
    y = src[L['src']][int(L['a']*SR):int(L['b']*SR)]
    i = int(L['t0']*SR); tracks[L['who']][i:i+len(y)] += y
boom = librosa.load('/home/claude/gta/boom.mp3', sr=SR)[0]*0.35
for L in LINES:
    if L['who'] == 'N' and L['idx'] in (1, 2):
        i = max(0, int((L['t0']-0.25)*SR)); n = min(len(boom), N-i); fx[i:i+n] += boom[:n]
mix = tracks['G']*1.0 + tracks['S']*1.0 + tracks['N']*0.95 + fx
mix = mix/np.max(np.abs(mix))*0.9
sf.write('mix.wav', mix, SR)
hop = SR//FPS
def rms(x):
    n = len(x)//hop; return np.sqrt((x[:n*hop].reshape(n, hop)**2).mean(1))
RMS = {k: rms(v) for k, v in tracks.items()}
for k in RMS:
    m = np.percentile(RMS[k][RMS[k] > 1e-4], 90) if (RMS[k] > 1e-4).any() else 1
    RMS[k] = RMS[k]/m

def mouth_level(who, n):
    r = RMS[who]
    if n >= len(r): return 0
    v = r[n]
    return 0 if v < 0.12 else 1 if v < 0.4 else 2 if v < 0.75 else 3

# ---------------- line direction ----------------
# per line: (shot, G expr, S expr, G arm, S arm, insert)
DIR = {
 'S0': ('wide', 'normal', 'angry', 'hold', 'show', None),
 'G0': ('cuG', 'angry', 'smug', 'hold', 'show', None),
 'S1': ('cuS', 'normal', 'angry', 'hold', 'show', None),
 'G1': ('cuG', 'smug', 'normal', 'show', 'hold', None),
 'S2': ('cuS', 'smug', 'angry', 'show', 'hold', None),
 'G2': ('cuG', 'angry', 'angry', 'hold', 'hold', None),
 'S3': ('wide', 'angry', 'angry', 'hold', 'show', None),
 'G3': ('cuG', 'angry', 'angry', 'show', 'hold', None),
 'S4': ('cuS', 'normal', 'angry', 'hold', 'show', None),
 'G4': ('cuG', 'smug', 'angry', 'show', 'hold', None),
 'S5': ('cuS', 'normal', 'angry', 'hold', 'show', None),
 'G5': ('cuG', 'angry', 'angry', 'show', 'hold', 'moon'),
 'S6': ('cuS', 'normal', 'angry', 'hold', 'hold', None),
 'G6': ('cuG', 'smug', 'angry', 'show', 'hold', None),
 'S7': ('wide', 'smug', 'angry', 'hold', 'show', None),
 'G7': ('cuG', 'angry', 'angry', 'show', 'hold', None),
 'G8': ('cuG', 'smug', 'angry', 'hold', 'hold', 'asphalt'),
 'S8': ('cuS', 'normal', 'angry', 'hold', 'show', None),
 'G9': ('cuG', 'smug', 'angry', 'show', 'hold', None),
 'RING': ('wide', 'normal', 'normal', 'show', 'hold', None),
 'G10': ('call', 'smug', 'normal', 'show', 'hold', None),
 'S9': ('cuS', 'angry', 'angry', 'hold', 'show', None),
 'X0': ('cuG', 'angry', 'angry', 'show', 'show', None),
 'X1': ('wide', 'angry', 'angry', 'throw', 'show', None),
 'THROW': ('throw', 'angry', 'dead', 'throw', 'none', None),
 'S10': ('dying', 'angry', 'dead', 'none', 'none', None),
 }

# ---------------- backgrounds ----------------
def make_bg():
    im = Image.new('RGB', (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):
        k = y/1100
        c = (int(70+150*min(1, k)), int(60+70*min(1, k)), int(120-20*min(1, k)))
        d.line((0, y, W, y), fill=c)
    # panel building
    d.rectangle((-20, 260, 1100, 1420), fill=(150, 150, 165), outline=(20, 18, 22), width=8)
    for r in range(7):
        for c in range(6):
            x = 40 + c*175; y = 300 + r*150
            lit = (r*7 + c*3) % 5 == 0
            d.rectangle((x, y, x+110, y+95), fill=(255, 220, 120) if lit else (70, 90, 120), outline=(20, 18, 22), width=6)
            d.line((x+55, y, x+55, y+95), fill=(20, 18, 22), width=4)
    # entrance
    d.rectangle((420, 1120, 660, 1420), fill=(90, 60, 50), outline=(20, 18, 22), width=8)
    d.polygon([(380, 1120), (700, 1120), (680, 1070), (400, 1070)], fill=(110, 110, 120), outline=(20, 18, 22))
    d.ellipse((620, 1260, 640, 1280), fill=(230, 200, 80))
    # ground
    d.rectangle((0, 1420, W, H), fill=(95, 95, 102))
    d.line((0, 1420, W, 1420), fill=(20, 18, 22), width=8)
    d.line((120, 1700, 260, 1760), fill=(60, 60, 66), width=6); d.line((260, 1760, 330, 1740), fill=(60, 60, 66), width=6)
    # bench
    d.rectangle((40, 1380, 300, 1410), fill=(140, 90, 50), outline=(20, 18, 22), width=6)
    for x in (60, 270): d.rectangle((x, 1410, x+12, 1470), fill=(40, 40, 40))
    return im
BG = make_bg()
BGBLUR = BG.filter(ImageFilter.GaussianBlur(6))
_big = BGBLUR.resize((int(W*1.6), int(H*1.6)))
CUBG = {w: _big.crop((x, int(H*0.35), x+W, int(H*0.35)+H)) for w, x in (('G', 0), ('S', int(W*0.6)))}

def font(sz): return ImageFont.truetype(FB, sz)

def rays(t, c1, c2, rot=0.3):
    im = Image.new('RGB', (W, H), c2); d = ImageDraw.Draw(im); cx, cy = W/2, H*0.47
    for k in range(18):
        a0 = t*rot + k*2*math.pi/18; a1 = a0 + math.pi/18
        d.polygon([(cx, cy), (cx+3000*math.cos(a0), cy+3000*math.sin(a0)), (cx+3000*math.cos(a1), cy+3000*math.sin(a1))], fill=c1)
    return im

def big_phone(scale, glow=True):
    im = Image.new('RGBA', (int(260*scale), int(420*scale)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    redmi(d, im.width/2, im.height/2, scale); return im

def text_c(d, s, y, sz, fill=(255, 255, 255), stroke=10):
    f = font(sz); w = d.textlength(s, font=f)
    d.text(((W-w)/2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(15, 12, 18))

PH = big_phone(3.0)
def card_title(lt):
    im = rays(lt, (60, 30, 90), (30, 15, 50)); d = ImageDraw.Draw(im)
    g = sprite('G', 0, 0, 'angry', 1, 'show', 1100); s = sprite('S', 0, 0, 'smug', -1, 'show', 1100)
    off = int(120*max(0, 1-lt*3))
    im.paste(g, (-160-off, 760), g); im.paste(s, (W-s.width+160+off, 760), s)
    text_c(d, 'ГОША', 560, 120, (120, 230, 130)); text_c(d, 'VS', 690, 90); text_c(d, 'САНЯ', 790, 120, (250, 215, 90))
    return im
def card_spec(lt):
    im = rays(lt, (255, 120, 20), (230, 60, 10), 0.6); d = ImageDraw.Draw(im)
    z = 1 + 0.05*math.sin(lt*6)
    p = PH.resize((int(PH.width*z), int(PH.height*z))); im.paste(p, (int(W/2-p.width/2), int(H*0.47-p.height/2)), p)
    text_c(d, 'REDMI 9A', 1500, 130, (255, 255, 255))
    if lt > 1.3: text_c(d, 'ГОД: 2020', 1660, 70, (255, 240, 150), 8)
    if lt > 3.2: text_c(d, 'СКОРОСТЬ: ???', 1760, 70, (255, 240, 150), 8)
    return im
def card_final(lt):
    im = rays(lt, (255, 200, 40), (240, 120, 20), 0.5); d = ImageDraw.Draw(im)
    z = 1.0 + 0.15*min(1, lt/0.6)
    p = PH.resize((int(PH.width*z), int(PH.height*z))); im.paste(p, (int(W/2-p.width/2), int(H*0.45-p.height/2)), p)
    text_c(d, 'REDMI 9A', 1480, 140)
    text_c(d, '№1 В МИРЕ', 1640, 90, (255, 245, 170))
    # crying iPhone Duo in the corner
    ip = Image.new('RGBA', (360, 360), (0, 0, 0, 0)); iphone_duo(ImageDraw.Draw(ip), 180, 180, 0.9)
    ip = ip.rotate(-25, expand=True); im.paste(ip, (W-330, 1680), ip)
    return im
def ins_moon(lt):
    im = Image.new('RGB', (W, H), (8, 8, 20)); d = ImageDraw.Draw(im)
    rs = np.random.RandomState(3)
    for _ in range(160):
        x, y = rs.randint(0, W), rs.randint(0, H); d.ellipse((x, y, x+4, y+4), fill=(255, 255, 255))
    z = 1 + 0.08*lt; r = 330*z
    d.ellipse((W/2-r, 820-r, W/2+r, 820+r), fill=(235, 235, 220), outline=(15, 12, 18), width=8)
    for dx, dy, rr in [(-120, -80, 70), (90, 40, 55), (-30, 150, 40), (140, -150, 35), (-180, 90, 30)]:
        d.ellipse((W/2+dx*z-rr*z, 820+dy*z-rr*z, W/2+dx*z+rr*z, 820+dy*z+rr*z), fill=(200, 200, 185))
    text_c(d, 'СНЯТО НА REDMI 9A', 1260, 70, (255, 255, 255), 8)
    if lt > 0.6:
        d.rounded_rectangle((90, 1420, W-90, 1640), radius=40, fill=(245, 245, 250), outline=(15, 12, 18), width=6)
        f = font(52); d.text((140, 1450), 'NASA', font=f, fill=(20, 60, 160))
        d.text((140, 1530), 'КАК ВЫ ЭТО СНЯЛИ???', font=font(46), fill=(20, 20, 25))
    return im
def ins_asphalt(lt):
    im = Image.new('RGB', (W, H), (110, 110, 118)); d = ImageDraw.Draw(im)
    rs = np.random.RandomState(5); cx, cy = W/2, 1000
    d.ellipse((cx-420, cy-180, cx+420, cy+180), fill=(70, 70, 76), outline=(15, 12, 18), width=8)
    for k in range(14):
        a = rs.rand()*2*math.pi; L = 400 + rs.rand()*500
        pts = [(cx, cy)]; x, y = cx, cy
        for s in range(5):
            x += math.cos(a + rs.randn()*0.3)*L/5; y += math.sin(a + rs.randn()*0.3)*L/5*0.8; pts.append((x, y))
        d.line(pts, fill=(25, 25, 30), width=10)
    sh = 1 if lt < 0.3 else 0
    p = big_phone(1.6).rotate(70, expand=True); im.paste(p, (int(cx-p.width/2)+sh*12, int(cy-p.height/2)-60), p)
    for k in range(4):
        a = lt*3 + k*1.57; x = cx + 260*math.cos(a); y = cy - 80 + 120*math.sin(a)
        d.polygon([(x, y-30), (x+10, y-10), (x+30, y), (x+10, y+10), (x, y+30), (x-10, y+10), (x-30, y), (x-10, y-10)], fill=(255, 255, 200))
    text_c(d, '0 ЦАРАПИН', 1400, 110, (130, 255, 140))
    return im
def ins_call(lt, ring):
    im = Image.new('RGB', (W, H), (20, 20, 28)); d = ImageDraw.Draw(im)
    sh = int(10*math.sin(lt*70)) if ring else 0
    d.rounded_rectangle((180+sh, 330, 900+sh, 1700), radius=70, fill=(55, 58, 66), outline=(15, 12, 18), width=10)
    d.rounded_rectangle((215+sh, 400, 865+sh, 1630), radius=30, fill=(30, 110, 200))
    d.ellipse((440+sh, 560, 640+sh, 760), fill=(220, 220, 230), outline=(15, 12, 18), width=6)
    d.text((500+sh, 600), '?', font=font(120), fill=(80, 80, 90))
    f = font(70); s = 'ИЛОН МАСК'; w = d.textlength(s, font=f); d.text((540-w/2+sh, 820), s, font=f, fill=(255, 255, 255))
    f2 = font(44); s2 = 'входящий вызов'; w2 = d.textlength(s2, font=f2); d.text((540-w2/2+sh, 920), s2, font=f2, fill=(220, 230, 255))
    d.ellipse((290+sh, 1360, 440+sh, 1510), fill=(230, 60, 60)); d.ellipse((640+sh, 1360, 790+sh, 1510), fill=(60, 200, 90))
    return im

# ---------------- characters on set ----------------
def blink(n, who):
    p = 97 if who == 'G' else 131; return (n + (0 if who == 'G' else 40)) % p < 4

def scene(n, shot, cfg, speaker, lt):
    _, ge, se, ga, sa, _ = cfg
    gm = mouth_level('G', n) if speaker == 'G' else 0
    sm = mouth_level('S', n) if speaker == 'S' else 0
    bob = lambda who: int(6*math.sin(n*0.5)) if speaker == who and (gm if who == 'G' else sm) else 0
    if shot in ('wide', 'call'):
        im = BG.copy(); h = 1150
        g = sprite('G', gm, int(blink(n, 'G')), ge, 1, ga, h); s = sprite('S', sm, int(blink(n, 'S')), se, -1, sa, h)
        im.paste(g, (40, 1830-h + bob('G')), g); im.paste(s, (W-s.width-40, 1830-h + bob('S')), s)
        return im
    who = 'G' if shot == 'cuG' else 'S'
    im = CUBG[who].copy()
    h = 2350
    if who == 'G':
        o = sprite('S', 0, int(blink(n, 'S')), se, -1, sa, h)
        im.paste(o, (W-260, 380), o)
        c = sprite('G', gm, int(blink(n, 'G')), ge, 1, ga, h); im.paste(c, (int(W/2-c.width/2)-60, 260 + bob('G')), c)
    else:
        o = sprite('G', 0, int(blink(n, 'G')), ge, 1, ga, h)
        im.paste(o, (-o.width+260, 380), o)
        c = sprite('S', sm, int(blink(n, 'S')), se, -1, sa, h); im.paste(c, (int(W/2-c.width/2)+60, 260 + bob('S')), c)
    return im

def throw_scene(n, lt):
    im = BG.copy(); h = 1150; d = ImageDraw.Draw(im)
    g = sprite('G', 0, 0, 'angry', 1, 'throw', h); im.paste(g, (40, 1830-h), g)
    hit = 0.45
    sx0 = W - sprite('S', 0, 0, 'angry', -1, 'show', h).width - 40
    if lt < hit:
        s = sprite('S', 0, 0, 'angry', -1, 'show', h); im.paste(s, (sx0, 1830-h), s)
        u = lt/hit; x0, y0 = 300, 900; x1, y1 = sx0 + s.width*0.5, 1830-h+260
        x = x0 + (x1-x0)*u; y = y0 + (y1-y0)*u - 260*math.sin(math.pi*u)
        p = big_phone(0.9).rotate(-lt*1500, expand=True); im.paste(p, (int(x-p.width/2), int(y-p.height/2)), p)
    else:
        u = min(1, (lt-hit)/0.45); ang = -85*u*u
        s = sprite('S', 0, 0, 'dead', -1, 'none', h).rotate(ang, expand=True, center=None)
        tx = W - s.width + 30; im.paste(s, (int(sx0 + (tx - sx0)*u), 1830 - s.height + int(40*u)), s)
        p = big_phone(0.9).rotate(30, expand=True); im.paste(p, (sx0 + 120 + int(200*u), 1700), p)
        if lt - hit < 0.6:
            k = (lt - hit)/0.6; cx, cy = sx0 + 300, 950
            r = 260*(0.6 + 0.6*k)
            pts = [(cx + (r if q % 2 == 0 else r*0.55)*math.cos(q*math.pi/8), cy + (r if q % 2 == 0 else r*0.55)*math.sin(q*math.pi/8)) for q in range(16)]
            d.polygon(pts, fill=(255, 230, 60), outline=(15, 12, 18))
            f = font(120); w = d.textlength('БАМ!', font=f); d.text((cx - w/2, cy - 70), 'БАМ!', font=f, fill=(230, 40, 40), stroke_width=8, stroke_fill=(15, 12, 18))
        if lt - hit < 0.3:
            k = int(30*(1 - (lt-hit)/0.3)); im = im.transform(im.size, Image.AFFINE, (1, 0, k*math.sin(lt*90), 0, 1, k*math.cos(lt*80)))
    return im

def dying_scene(n, lt):
    im = Image.new('RGB', (W, H), (95, 95, 102)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 700), fill=(150, 150, 165))
    for c in range(6): d.rectangle((40+c*175, 300, 150+c*175, 395), fill=(70, 90, 120), outline=(20, 18, 22), width=6)
    d.line((0, 700, W, 700), fill=(20, 18, 22), width=8)
    s = sprite('S', 0, 0, 'dead', -1, 'none', 1900).rotate(-90, expand=True)
    jit = int(4*math.sin(n*1.7))
    im.paste(s, (W - s.width + 90 + jit, 820), s)
    p = big_phone(1.1).rotate(15, expand=True); im.paste(p, (W - 620, 1000), p)
    for k in range(5):
        a = lt*4 + k*1.256; x = W - 260 + 150*math.cos(a); y = 860 + 50*math.sin(a)
        d.polygon([(x, y-26), (x+8, y-8), (x+26, y), (x+8, y+8), (x, y+26), (x-8, y+8), (x-26, y), (x-8, y-8)], fill=(255, 230, 60), outline=(15, 12, 18))
    return im

# ---------------- captions ----------------
def chunks(text, t0, t1):
    words = text.replace('—', '').split()
    vow = lambda w: max(1, len(re.findall('[аеёиоуыэюяАЕЁИОУЫЭЮЯaeiouAEIOU]', w)))
    groups, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) == 2 or w[-1] in '.,!?…' or len(' '.join(cur)) > 14: groups.append(cur); cur = []
    if cur: groups.append(cur)
    tot = sum(vow(w) for g in groups for w in g) + 0.0
    out, t = [], t0 + 0.05; span = (t1 - t0 - 0.12)
    for g in groups:
        d = span*sum(vow(w) for w in g)/tot; out.append((t, t+d, ' '.join(g).upper())); t += d
    return out
CAPS = []
for L in LINES:
    if L['who'] not in ('RING', 'THROW'): CAPS += chunks(L['text'], L['t0'], L['t1'])
CF = font(84)
def caption(im, t):
    for a, b, s in CAPS:
        if a <= t < b:
            d = ImageDraw.Draw(im); f = CF; w = d.textlength(s, font=f)
            while w > 1000: f = ImageFont.truetype(FB, f.size-6); w = d.textlength(s, font=f)
            k = min(1, (t-a)/0.08); sz = 1.0 + 0.15*(1-k)
            d.text(((W-w)/2, 250), s, font=f, fill=(255, 255, 255), stroke_width=10, stroke_fill=(10, 8, 12))
            return

# ---------------- main loop ----------------
def line_at(t):
    cur = None
    for L in LINES:
        if L['t0'] - 0.18 <= t: cur = L
    return cur

def frame(n):
    t = n/FPS; L = line_at(t)
    if L is None: L = LINES[0]
    lt = t - L['t0']
    if L['who'] == 'N':
        im = [card_title, card_spec, card_final][L['idx']](max(0, lt))
    else:
        key = L['key']
        cfg = DIR[key]; shot = cfg[0]; ins = cfg[5]
        dur = L['t1'] - L['t0']
        if shot == 'throw':
            im = throw_scene(n, lt)
        elif shot == 'dying':
            im = dying_scene(n, lt)
        elif key == 'G10' and lt < dur*0.55 or key == 'RING' and lt > 0.6:
            im = ins_call(lt, key == 'RING')
        elif ins and lt > dur*0.45:
            im = {'moon': ins_moon, 'asphalt': ins_asphalt}[ins](lt - dur*0.45)
        else:
            im = scene(n, 'wide' if shot == 'call' else shot, cfg, L['who'], lt)
        # punch-in at the start of an angry line
        if (L['who'] == 'G' and cfg[1] == 'angry' or L['who'] == 'S' and cfg[2] == 'angry') and shot not in ('throw', 'dying') and 0 <= lt < 0.25:
            z = 1 + 0.06*(1 - lt/0.25)
            im = im.resize((int(W*z), int(H*z))).crop((int(W*(z-1)/2), int(H*(z-1)/2), int(W*(z-1)/2)+W, int(H*(z-1)/2)+H))
    caption(im, t)
    a = np.asarray(im.convert('RGB'))
    fo = min(1, (DUR - t)/0.5)
    return (a*fo).astype(np.uint8) if fo < 1 else a

if PREVIEW:
    ts = [ (L['t0']+L['t1'])/2 for L in LINES ]
    tiles = [Image.fromarray(frame(int(x*FPS))).resize((216, 384)) for x in ts]
    sh = Image.new('RGB', (216*9, 384*((len(tiles)+8)//9)))
    for k, tl in enumerate(tiles): sh.paste(tl, ((k % 9)*216, (k//9)*384))
    sh.save('prev.jpg'); sys.exit()
NF = int(DUR*FPS)
cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', 'mix.wav',
       '-map', '0:v', '-map', '1:a', '-t', str(DUR), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
       '-movflags', '+faststart', 'gosha_sanya.mp4']
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for n in range(NF): p.stdin.write(frame(n).tobytes())
p.stdin.close(); p.wait()
