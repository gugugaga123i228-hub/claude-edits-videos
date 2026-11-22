# list candidate shots (face present, steady, no cut) as a numbered crop sheet
import sys, json, cv2, numpy as np
scan = json.load(open(sys.argv[1])); src = sys.argv[2]; out = sys.argv[3]; dmin = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
fr = scan['frames']; st = scan['step']; asp = scan['aspect']; cw = 0.5625/asp; lb = scan['lb']
c = []
i = 0
while i < len(fr):
    j = i
    while j < len(fr) and fr[j]['fx'] is not None and fr[j]['fh'] > 0.09 and (j == i or fr[j]['diff'] < 28) and abs(fr[j]['fx'] - fr[i]['fx']) < cw*0.25:
        j += 1
    if (j - i) * st >= dmin and np.mean([f['bri'] for f in fr[i:j]]) > 35:
        seg = fr[i:j]
        c.append(dict(t=seg[0]['t'] + 0.1, len=round((j-i)*st, 2), cx=float(np.median([f['fx'] for f in seg])), fh=float(np.mean([f['fh'] for f in seg]))))
    i = max(j, i+1)
cap = cv2.VideoCapture(src); tiles = []
for n, s in enumerate(c):
    cap.set(cv2.CAP_PROP_POS_MSEC, (s['t'] + min(0.5, s['len']/2))*1000); ok, f = cap.read()
    if not ok: continue
    if lb: h = f.shape[0]; f = f[int(h*lb):int(h*(1-lb))]
    h, w = f.shape[:2]; ww = int(h*9/16); x = int(min(max(s['cx']*w - ww/2, 0), w-ww))
    t = cv2.resize(f[:, x:x+ww], (108, 192))
    cv2.putText(t, str(n), (3, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2); tiles.append(t)
cols = 16; rows = (len(tiles)+cols-1)//cols; sh = np.zeros((rows*192, cols*108, 3), np.uint8)
for n, t in enumerate(tiles): r, k = divmod(n, cols); sh[r*192:(r+1)*192, k*108:(k+1)*108] = t
cv2.imwrite(out, sh); json.dump(c, open(out + '.json', 'w')); print(len(c))
