# Build an edit30 config from beat slots + a curated list of candidate shots.
# usage: python3 assemble.py spec.json out.json   (spec: aud, src, sf, lb, drop, pre, post, pattern_pre, pattern_post,
#         cands (json from cands.py), ids [ordered ids to use; reused cyclically if short], accents_every, strobe, flash, sat, con, gain, sp_pre)
import sys, json, numpy as np, librosa
S = json.load(open(sys.argv[1])); C = json.load(open(S['cands']))
y, sr = librosa.load(S['aud'], sr=22050, mono=True)
_, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
bi = int(np.argmin(np.abs(beats - S['drop']))); drop = beats[bi]; s0 = drop - S['pre']
bt = [b - s0 for b in beats if s0 - 1e-6 <= b <= drop + S['post']]
pre = [b for b in bt if b < S['pre'] - 1e-3]; post = [b for b in bt if b >= S['pre'] - 1e-3]
seq = []
j = p = 0; pp = S.get('pattern_pre', [2])
while j < len(pre): seq.append((pre[j], False)); j += pp[p % len(pp)]; p += 1
j = p = 0; pq = S.get('pattern_post', [2])
while j < len(post) - 1: seq.append((post[j], True)); j += pq[p % len(pq)]; p += 1
if seq: seq[0] = (0.0, seq[0][1])
fin = post[-1]
ids = S['ids']; cw = 0.5625 / S.get('aspect', 16/9)
use = {}
cuts = []
for n, (t0, isp) in enumerate(seq):
    t1 = seq[n+1][0] if n+1 < len(seq) else fin
    c = C[ids[n % len(ids)]]; k = use.get(ids[n % len(ids)], 0); use[ids[n % len(ids)]] = k + 1
    need = t1 - t0
    sp = 1.0 if isp else S.get('sp_pre', 1.0)
    st = c['t'] + 0.15 + k * need            # reuse a shot -> take a later part of it
    avail = c['t'] + c['len'] - 0.1 - st
    if avail < need * sp: sp = max(0.35, avail / need) if avail > 0.2 else 0.5; st = min(st, c['t'] + 0.1)
    cx = min(max(c['cx'], cw/2), 1 - cw/2)
    acc = isp and ((n - len(pre)) % S.get('accents_every', 4) == 0)
    cuts.append([round(t0, 3), round(t1, 3), round(st, 2), round(cx, 3), round(sp, 3), bool(acc), bool(isp)])
cfg = dict(aud=S['aud'], src=S['src'], sf=S['sf'], lb=S.get('lb', 0), s0=round(float(s0), 3), dur=round(fin + 1.4, 2), cuts=cuts,
           strobe=[[max(0, S['pre'] - 1.3), S['pre']]] if S.get('strobe', True) else [], flash=S.get('flash', True),
           sat=S.get('sat', 1.1), con=S.get('con', 0.2), gain=S.get('gain', 1.0))
json.dump(cfg, open(sys.argv[2], 'w')); print('slots', len(seq), 'ids', len(ids), 'dur', cfg['dur'])
