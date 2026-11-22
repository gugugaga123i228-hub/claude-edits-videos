# Auto-plan an edit: beat-synced cuts from the song + face-aware shot picking from a scanned pack.
# usage: python3 plan.py spec.json out_cfg.json
# spec: {scan, src, sf, aud, drop (song time), pre (seconds before drop), post (seconds after drop),
#        pattern_pre [beats per cut], pattern_post [...], accents_every, sat, con, gain, strobe(bool),
#        flash(bool), skip [[a,b],..] source ranges to avoid, min_face}
import sys, json, numpy as np, librosa
S = json.load(open(sys.argv[1])); scan = json.load(open(S['scan']))
fr = scan['frames']; step = scan['step']; asp = scan['aspect']
cropw = 0.5625 / asp                      # crop width as fraction of frame width
y, sr = librosa.load(S['aud'], sr=22050, mono=True)
_, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
drop = S['drop']; s0 = drop - S['pre']; end = drop + S['post']
# snap drop to nearest beat
bi = int(np.argmin(np.abs(beats - drop))); drop_b = beats[bi]
s0 = drop_b - S['pre']
bt = [b - s0 for b in beats if s0 - 1e-6 <= b <= end]
if not bt or bt[0] > 0.05: bt = [0.0] + bt
dropt = drop_b - s0
# build cut times
cuts_t = []; i = 0; pre_pat = S.get('pattern_pre', [4]); post_pat = S.get('pattern_post', [2])
k = 0
pre_beats = [b for b in bt if b < dropt - 1e-3]
post_beats = [b for b in bt if b >= dropt - 1e-3]
seq = []
j = 0; p = 0
while j < len(pre_beats):
    n = pre_pat[p % len(pre_pat)]; seq.append((pre_beats[j], False)); j += n; p += 1
j = 0; p = 0
while j < len(post_beats) - 1:
    n = post_pat[p % len(post_pat)]; seq.append((post_beats[j], True)); j += n; p += 1
seq[0] = (0.0, seq[0][1])
fin = post_beats[-1] if post_beats else bt[-1]
# candidate scoring
times = np.array([f['t'] for f in fr])
def window(st, d):
    a = int(st / step); b = int((st + d) / step) + 1
    return fr[a:b]
skip = S.get('skip', [])
RELAX = [1.0]
import cv2
VER = None
if S.get('paint'):
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision
    _fd = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
        base_options=mpt.BaseOptions(model_asset_path='/home/claude/models/face.tflite'), min_detection_confidence=0.35))
    _cap = cv2.VideoCapture(S['src']); _vc = {}
    def VER(st):
        k = round(st, 2)
        if k in _vc: return _vc[k]
        _cap.set(cv2.CAP_PROP_POS_MSEC, st*1000); ok, f = _cap.read(); res = False
        if ok:
            lb = scan['lb']
            if lb: h = f.shape[0]; f = f[int(h*lb):int(h*(1-lb))]
            rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
            for d in _fd.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)).detections:
                b = d.bounding_box; roi = f[max(0,b.origin_y):b.origin_y+b.height, max(0,b.origin_x):b.origin_x+b.width]
                if roi.size == 0: continue
                hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                white = ((hsv[:,:,1] < 60) & (hsv[:,:,2] > 120)).mean()
                if white > S.get('paint_frac', 0.25): res = True
        _vc[k] = res; return res
def score(st, d):
    rf = RELAX[0]
    w = window(st, d)
    if len(w) < 2: return -1, None
    if any(a <= st <= b or a <= st + d <= b for a, b in skip): return -1, None
    if max(x['diff'] for x in w[1:]) > S.get('cut_diff', 28): return -1, None   # scene change inside
    req = S.get('require', 'face+person')
    for x in w:
        if x['fx'] is None: return -1, None
        if req == 'face+person' and (x['px'] is None or abs(x['px'] - x['fx']) > 0.2): return -1, None
    xs = [x['fx'] for x in w]; hs = [x['fh'] for x in w]
    if min(hs) < S.get('min_face', 0.12) * rf: return -1, None
    if np.std(xs) > cropw * 0.18: return -1, None
    bri = np.mean([x['bri'] for x in w]); sh = np.mean([x['sharp'] for x in w])
    if bri < S.get('min_bri', 35) * rf: return -1, None
    sc = np.mean(hs) * (1 + min(sh, 400) / 400) * (0.6 if bri < 55 else 1.0)
    return sc, float(np.median(xs))
slots = []
for n, (t0, post) in enumerate(seq):
    t1 = seq[n + 1][0] if n + 1 < len(seq) else fin
    slots.append([t0, t1, post])
used = []
picks = []
cands = []
sp_pre = S.get('sp_pre', 1.0)
for st in np.arange(0.3, scan['dur'] - 3, step):
    cands.append(st)
for t0, t1, post in slots:
    d = (t1 - t0) * (1.0 if post else sp_pre) + 0.1
    best = None
    for st in cands:
        if any(abs(st - u) < S.get('gap', 4.0) for u in used): continue
        sc, cx = score(st, d)
        if sc > 0 and (best is None or sc > best[0]):
            if VER is None or (VER(st + d*0.3) and VER(st + d*0.8)): best = (sc, st, cx)
    if best is None:
        for st in cands:
            if any(abs(st - u) < 1.2 for u in used): continue
            sc, cx = score(st, d)
            if sc > 0 and (best is None or sc > best[0]): best = (sc, st, cx)
    if best is None:
        for rf in (0.8, 0.6, 0.4):
            RELAX[0] = rf
            for st in cands:
                if any(abs(st - u) < 2.0 for u in used): continue
                sc, cx = score(st, d)
                if sc > 0 and (best is None or sc > best[0]): best = (sc, st, cx)
            if best: break
        RELAX[0] = 1.0
    if best is None: raise SystemExit(f'no shot for slot {t0:.2f}')
    used.append(best[1]); picks.append((best[1], best[2]))
# keep story order: sort picks of post section by source time, keep the biggest face for the drop
pre_n = sum(1 for s in slots if not s[2])
post_picks = sorted(picks[pre_n:], key=lambda p: p[0]) if S.get('chrono', True) else picks[pre_n:]
picks = picks[:pre_n] + post_picks
cuts = []
acc_every = S.get('accents_every', 4)
for n, ((t0, t1, post), (st, cx)) in enumerate(zip(slots, picks)):
    lo, hi = cropw / 2, 1 - cropw / 2
    cxn = min(max(cx, lo), hi)
    cuts.append([round(t0, 3), round(t1, 3), round(float(st), 2), round(cxn, 3), 1.0 if post else sp_pre,
                 bool(post and ((n - pre_n) % acc_every == 0)), bool(post)])
dur = round(fin + 1.4, 2)
cfg = dict(aud=S['aud'], src=S['src'], sf=S['sf'], lb=scan['lb'], s0=round(s0, 3), dur=dur, cuts=cuts,
           strobe=[[max(0, dropt - 1.3), dropt]] if S.get('strobe', True) else [], flash=S.get('flash', True),
           sat=S.get('sat', 1.1), con=S.get('con', 0.2), gain=S.get('gain', 1.0))
json.dump(cfg, open(sys.argv[2], 'w'))
print('cuts', len(cuts), 'dur', dur, 'drop at', round(dropt, 2), 'tempo', round(60 / np.median(np.diff(beats)), 1))
