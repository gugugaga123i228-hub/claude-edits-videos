# shrink each clip's speed so it never runs past a hard cut in its source
import json, sys, numpy as np, cv2
P = sys.argv[1]; c = json.load(open(P))
caps = [cv2.VideoCapture(s[0]) for s in c['srcs']]
def end(k):
    t0, t1, si, st, cx, vmin, vmax = k[:7]; xs = np.linspace(0, 1, 200); v = vmin+(vmax-vmin)*np.abs(2*xs-1)**1.6
    return st+np.trapezoid(v, xs)*(t1-t0)
def firstcut(si, a, b):
    cap = caps[si]; cap.set(0, a*1000); prev = None; t = a
    while t < b:
        ok, f = cap.read()
        if not ok: break
        f = cv2.resize(f, (64, 36)).astype(float)
        if prev is not None and np.abs(f-prev).mean() > 35: return t
        prev = f; t += 1/30
    return None
for k in c['cuts']:
    if k[6] == 0: continue
    ct = firstcut(k[2], k[3], end(k)+0.2)
    if ct is not None:
        lim = ct-0.07
        while end(k) > lim and k[6] > k[5]+0.05: k[6] = round(k[6]-0.05, 3)
        while end(k) > lim and k[5] > 0.05: k[5] = round(k[5]-0.02, 3); k[6] = max(k[6], k[5])
        print('fit', k[0], k[3], k[5], k[6], round(end(k), 2), round(ct, 2))
json.dump(c, open(P, 'w'))
