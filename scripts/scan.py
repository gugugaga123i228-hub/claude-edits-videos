# Scan a footage pack: every STEP seconds detect faces/persons, sharpness, brightness.
# usage: python3 scan.py pack.mp4 out.json [lb] [step]
import sys, json, cv2, numpy as np, mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision
src, out = sys.argv[1], sys.argv[2]
LB = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
STEP = float(sys.argv[4]) if len(sys.argv) > 4 else 0.25
M = '/home/claude/models/'
fd = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
    base_options=mpt.BaseOptions(model_asset_path=M+'face.tflite'), min_detection_confidence=0.35))
od = vision.ObjectDetector.create_from_options(vision.ObjectDetectorOptions(
    base_options=mpt.BaseOptions(model_asset_path=M+'det.tflite'), score_threshold=0.35,
    category_allowlist=['person'], max_results=4))
cap = cv2.VideoCapture(src); fps = cap.get(cv2.CAP_PROP_FPS) or 30
n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); dur = n / fps
res = []; t = 0.0; prev = None
while t < dur - 0.1:
    cap.set(cv2.CAP_PROP_POS_MSEC, t*1000); ok, f = cap.read()
    if not ok: break
    if LB: h = f.shape[0]; f = f[int(h*LB):int(h*(1-LB))]
    h, w = f.shape[:2]; s = 640 / w; sm = cv2.resize(f, (640, int(h*s)))
    rgb = cv2.cvtColor(sm, cv2.COLOR_BGR2RGB); im = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    H, W = sm.shape[:2]
    faces = [(d.bounding_box.origin_x + d.bounding_box.width/2, d.bounding_box.height, d.categories[0].score)
             for d in fd.detect(im).detections]
    pers = [(d.bounding_box.origin_x + d.bounding_box.width/2, d.bounding_box.height, d.categories[0].score)
            for d in od.detect(im).detections]
    g = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY)
    sharp = float(cv2.Laplacian(g, cv2.CV_64F).var()); bri = float(g.mean())
    diff = float(np.abs(g.astype(np.int16) - prev).mean()) if prev is not None and prev.shape == g.shape else 99.0
    prev = g.astype(np.int16)
    fc = max(faces, key=lambda x: x[1]) if faces else None
    pc = max(pers, key=lambda x: x[1]) if pers else None
    res.append(dict(t=round(t, 2), fx=round(fc[0]/W, 3) if fc else None, fh=round(fc[1]/H, 3) if fc else 0,
                    px=round(pc[0]/W, 3) if pc else None, ph=round(pc[1]/H, 3) if pc else 0,
                    nf=len(faces), sharp=round(sharp, 1), bri=round(bri, 1), diff=round(diff, 1)))
    t += STEP
json.dump(dict(src=src, lb=LB, dur=dur, step=STEP, aspect=w/h, frames=res), open(out, 'w'))
print(out, len(res), 'faces in', sum(1 for r in res if r['fx'] is not None), 'persons in', sum(1 for r in res if r['px'] is not None))
