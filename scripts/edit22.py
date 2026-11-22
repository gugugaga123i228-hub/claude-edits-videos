import sys, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

AUD = sys.argv[1]; OUT = sys.argv[2]; PREVIEW = len(sys.argv) > 3 and sys.argv[3] == 'preview'
W, H, FPS = 1080, 1920, 30
DUR = 27.0
N = int(round(DUR * FPS))
FB = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
FM = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
EM = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
ORG = (217, 119, 87)
WH = (255, 255, 255); BK = (0, 0, 0)

KICKS = [0.17, 0.53, 0.98, 1.29, 1.63, 1.83, 2.28, 2.69, 3.11, 3.54, 3.88, 4.19, 4.74, 5.05, 5.7, 6.13, 6.44,
         7.0, 7.31, 7.64, 7.86, 8.28, 8.72, 9.15, 9.58, 10.01, 10.44, 10.87, 11.3, 11.73, 12.16, 12.6, 13.03,
         13.46, 13.89]
HARD = [3.54, 3.88, 4.19, 5.05, 5.7, 6.13, 6.44] + KICKS[17:]

_fc = {}
def F(sz, path=FB):
    k = (sz, path)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, sz)
    return _fc[k]

_tc = {}
def tl(txt, size, fill=WH, stroke=0, sf=BK, path=FB, maxw=980):
    k = (txt, size, fill, stroke, sf, path, maxw)
    if k in _tc: return _tc[k]
    s = size
    while True:
        f = F(s, path); bb = f.getbbox(txt, stroke_width=stroke)
        if bb[2] - bb[0] <= maxw or s < 30: break
        s = int(s * 0.93)
    pad = stroke + 6
    im = Image.new('RGBA', (bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - bb[0], pad - bb[1]), txt, font=f, fill=fill + (255,), stroke_width=stroke, stroke_fill=sf + (255,))
    _tc[k] = im; return im

_ec = {}
def emo(ch, size=300):
    k = (ch, size)
    if k in _ec: return _ec[k]
    f = ImageFont.truetype(EM, 109)
    im = Image.new('RGBA', (160, 150), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox()); s = size / max(im.size)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    _ec[k] = im; return im

def put(img, lay, cx, cy, sc=1.0, al=1.0, rot=0):
    if al <= 0 or sc <= 0: return
    if abs(sc - 1) > 1e-3:
        lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BILINEAR)
    if rot: lay = lay.rotate(rot, expand=True, resample=Image.BILINEAR)
    if al < 1:
        a = lay.getchannel('A').point(lambda v: int(v * al)); lay = lay.copy(); lay.putalpha(a)
    img.paste(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)), lay)

def sl(ts, dur=0.16, big=1.9):
    if ts < 0: return 0, 0
    p = min(1, ts / dur); sc = 1 + (big - 1) * (1 - p) ** 2
    if ts > dur: sc = 1 + 0.05 * math.exp(-(ts - dur) * 9) * math.sin((ts - dur) * 38)
    return sc, min(1, ts / 0.04)

def pop(ts, dur=0.22):
    if ts < 0: return 0
    p = min(1, ts / dur)
    return 1 + 0.25 * math.sin(p * math.pi) * (1 - p) * 2 - (1 - p) ** 2 * 0.9 if p < 1 else 1 + 0.04 * math.exp(-(ts - dur) * 8) * math.sin((ts - dur) * 30)

def slamtxt(img, t, t0, txt, cy, size, fill=WH, stroke=0, sf=BK, path=FB, maxw=980, cx=W / 2):
    sc, al = sl(t - t0)
    if al > 0: put(img, tl(txt, size, fill, stroke, sf, path, maxw), cx, cy, sc, al)

def emopop(img, t, t0, ch, cx, cy, size, rot=0):
    sc = pop(t - t0)
    if sc > 0: put(img, emo(ch, size), cx, cy, sc, 1, rot)





SRC='/home/claude/vader/v3.mp4'; SRC2='/home/claude/vader/v5.mp4'
A0=0.0; B=0.5455
def T(k): return A0+B*k
RED=(225,30,45); BLUE=(90,170,255)
# (beat_start, beat_end, clip_start_sec, cx_frac)
CL=[(0,3,15.0,.5,0),(3,6,7.6,.5,0),
 (8,10,13.0,.5,1),(10,12,31.3,.58,1),(12,14,59.0,.55,1),
 (16,18,15.0,.5,1),(18,20,35.0,.6,1),(20,22,49.8,.55,1),
 (24,26,183.2,.55,0),(26,28,185.2,.55,0),(28,30,187.2,.55,0)]
BLK=[(6,8,'CHATGPT','ДЖЕДАЙ',BLUE),(14,16,'GEMINI','ТОЖЕ ДЖЕДАЙ',BLUE),(22,24,'CLAUDE','СИТХ',RED)]
PAY=[(211.3,.5),(213.2,.5),(248.2,.55),(249.4,.5),(253.4,.5),(257.4,.5),(266.5,.5),(279.3,.42),(288.5,.45),(192.4,.5),(180.2,.5),(200.3,.5),(244.4,.58),(129.3,.5),(63.0,.45),(120.5,.5)]
for i,(s,c) in enumerate(PAY): CL.append((30+i,31+i,s,c,0))
FIN=T(46)
caps=[cv2.VideoCapture(SRC),cv2.VideoCapture(SRC2)]; cache={}
def frames_for(ci):
    if ci in cache: return cache[ci]
    cache.clear()
    b0,b1,st,cx,sr=CL[ci]; n=int((b1-b0)*B*30)+4; cap=caps[sr]
    cap.set(cv2.CAP_PROP_POS_MSEC,st*1000)
    fr=[]
    for _ in range(n):
        ok,f=cap.read()
        if not ok: break
        fr.append(f)
    if not fr: fr=[np.zeros((1080,1920,3),np.uint8)]
    cache[ci]=fr; return fr
def vcrop(f,cx,z):
    h,w=f.shape[:2]; ch=h/z; cw=ch*9/16
    cxp=cx*w; cxp=min(max(cxp,cw/2),w-cw/2); x0=int(round(cxp-cw/2)); y0=int(round((h-ch)/2))
    c=f[y0:y0+int(round(ch)),x0:x0+int(round(cw))]
    o=cv2.resize(c,(1080,1920),interpolation=cv2.INTER_CUBIC)
    bl=cv2.GaussianBlur(o,(0,0),3); return cv2.addWeighted(o,1.6,bl,-0.6,0)
def black_idx(t):
    for i,(b0,b1,n,v,c) in enumerate(BLK):
        if T(b0)<=t<T(b1): return i
    return -1
def cut_index(t):
    for i,(b0,b1,_,_,_) in enumerate(CL):
        if t<T(b1)-1e-6: return i
    return len(CL)-1
def radial(d,cx,cy,col,ts,n=28):
    Rr=2400
    for k in range(n):
        a0=(k/n+ts*0.08)*2*math.pi; a1=a0+math.pi/n*0.55
        d.polygon([(cx,cy),(cx+Rr*math.cos(a0),cy+Rr*math.sin(a0)),(cx+Rr*math.cos(a1),cy+Rr*math.sin(a1))],fill=col)
def emopop(img,t,t0,ch,cx,cy,size,rot=0):
    sc=pop(t-t0)
    if sc>0: put(img,emo(ch,size),cx,cy,sc,1,rot)
def slamtxt(img,t,t0,txt,cy,size,fill=WH,stroke=0,sf=BK,path=FB,maxw=980,cx=W/2):
    sc,al=sl(t-t0)
    if al>0: put(img,tl(txt,size,fill,stroke,sf,path,maxw),cx,cy,sc,al)

def render(i):
    t=i/FPS
    if t>=FIN:
        img=Image.new('RGB',(W,H)); d=ImageDraw.Draw(img)
        d.rectangle([0,0,W,H],fill=(8,8,8)); radial(d,W/2,900,(40,12,14),t)
        slamtxt(img,t,FIN,'ИИ-ЭДИТЫ',820,200,WH,0)
        slamtxt(img,t,FIN+0.3,'@claude.edits2',1060,84,(235,235,240),0,BK,FM)
        a=np.asarray(img)[:,:,::-1].copy(); ts=t-FIN
    elif black_idx(t)>=0:
        bi=black_idx(t); b0,b1,nm,vd,col=BLK[bi]
        img=Image.new('RGB',(W,H)); d=ImageDraw.Draw(img)
        d.rectangle([0,0,W,H],fill=(4,4,6)); radial(d,W/2,960,tuple(int(x*0.16) for x in col),t)
        slamtxt(img,t,T(b0),nm,800,200,WH,0)
        slamtxt(img,t,T(b0+1),vd,1090,170 if len(vd)<8 else 130,col,0)
        a=np.asarray(img)[:,:,::-1].copy(); ts=(t-T(b0))%B
    else:
        ci=cut_index(t); b0,b1,st,cx,sr=CL[ci]; ts=t-T(b0)
        fr=frames_for(ci); lt=max(0,t-T(b0)); f=fr[min(len(fr)-1,int(lt*30))]
        dur=(b1-b0)*B
        a=vcrop(f,cx,1.0+0.10*min(1,lt/max(0.4,dur)))
        img=Image.fromarray(a[:,:,::-1])
        # text
        if t<T(6): slamtxt(img,t,0.3,'СИТХ ИЛИ ДЖЕДАЙ?',430,120,WH,7,BK)
        if t<T(6): slamtxt(img,t,T(2),'ИИ-ВЕРСИЯ',1550,80,ORG,5,BK)
        if T(30)<=t<T(38): slamtxt(img,t,T(30),'ТЁМНАЯ СТОРОНА',420,100,RED,7,BK)
        for (b0,b1,nm,vd,col) in BLK:
            if T(b1)<=t<T(b1+6): slamtxt(img,t,T(b1),vd,1600,120 if len(vd)<8 else 96,col,7,BK)
        a=np.asarray(img)[:,:,::-1].copy()
        bt=(t-A0)/B; ts=(bt-math.floor(bt))*B
    if T(6)<=t<T(22):
        a=a.astype(np.float32); a[:,:,0]*=1.12; a[:,:,2]*=0.92; a=np.clip(a,0,255).astype(np.uint8)
    hard = (t>=T(22))
    amp=0.075 if hard else 0.04
    z=1+amp*math.exp(-ts/0.1)
    sx=10*math.exp(-ts/0.08)*math.sin(i*2.7); sy=7*math.exp(-ts/0.08)*math.cos(i*3.1)
    M=np.float32([[z,0,W/2*(1-z)+sx],[0,z,H/2*(1-z)+sy]])
    a=cv2.warpAffine(a,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
    if ts<0.1 and t>=T(6):
        dx=int(20*math.exp(-ts/0.05)); a[:,:,0]=np.roll(a[:,:,0],dx,1); a[:,:,2]=np.roll(a[:,:,2],-dx,1)
    for fb in (23,30):
        if 0<=t-T(fb)<0.12: a=cv2.addWeighted(a,0.5,np.full_like(a,(40,40,255)),0.5,0)
    if t>=T(24) and t<FIN:
        a=a.astype(np.float32); a[:,:,2]*=1.08; a[:,:,0]*=0.92; a=np.clip(a,0,255).astype(np.uint8)
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    v=1-0.3*(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2)/2
    a=a.astype(np.float32)*v[:,:,None]
    a=(a-128)*1.08+128
    a+=np.random.RandomState(i).randn(H,W,1).astype(np.float32)*4
    a=np.clip(a,0,255).astype(np.uint8)
    f=min(1,(DUR-t)/0.3)
    if f<1: a=(a*max(0,f)).astype(np.uint8)
    return a

if PREVIEW:
    times=[0.4,1.5,2.5,3.6,4.5,5.2,6.6,8.2,10.6,13.0,15.0,17.5,19.5,21.5,22.8,24.0,26.2,28.0,32.0,25.5]
    tiles=[cv2.resize(render(int(x*FPS)),(180,320)) for x in times]
    cols=10; rows=2
    sheet=np.zeros((rows*320,cols*180,3),np.uint8)
    for n,tt in enumerate(tiles):
        r,c=divmod(n,cols); sheet[r*320:(r+1)*320,c*180:(c+1)*180]=tt
    cv2.imwrite(OUT,sheet); sys.exit()

cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
     '-i',AUD,'-map','0:v','-map','1:a','-c:v','libx264','-preset','medium','-crf','22','-maxrate','12M','-bufsize','24M',
     '-pix_fmt','yuv420p','-af','apad=pad_dur=2','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',OUT]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for i in range(N): p.stdin.write(render(i).tobytes())
p.stdin.close(); p.wait()
