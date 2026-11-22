import sys, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

AUD = sys.argv[1]; OUT = sys.argv[2]; PREVIEW = len(sys.argv) > 3 and sys.argv[3] == 'preview'
W, H, FPS = 1080, 1920, 30
DUR = 22.28
N = int(round(DUR * FPS))
FB = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
FM = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
EM = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
ORG = (217, 119, 87)
WH = (255, 255, 255); BK = (0, 0, 0)

import re, os
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

def rzoom(a,s,n=5):
    acc=np.zeros(a.shape,np.float32)
    for q in range(n):
        si=1+(s-1)*q/(n-1); M=np.float32([[si,0,W/2*(1-si)],[0,si,H/2*(1-si)]])
        acc+=cv2.warpAffine(a,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
    return (acc/n).astype(np.uint8)
PAL=[(255,120,200),(255,230,60),(80,220,255),(150,255,120),(255,140,40)]
def fx(a,typ,phase,p,seed):
    if p<=0.01: return a
    if typ=='zoom': return rzoom(a,1+0.55*p)
    if typ.startswith('whip'):
        sg=-1 if typ.endswith('l') else 1
        dx=(-sg if phase=='pre' else sg)*W*0.55*p*p
        M=np.float32([[1,0,dx],[0,1,0]]); a=cv2.warpAffine(a,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
        k=1+int(130*p); return cv2.blur(a,(k,1)) if k>1 else a
    if typ=='spin':
        ang=(14 if phase=='pre' else -14)*p; M=cv2.getRotationMatrix2D((W/2,H/2),ang,1+0.35*p)
        return cv2.warpAffine(a,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
    if typ=='rgb':
        dx=int(55*p); a=rzoom(a,1+0.10*p,3).copy(); a[:,:,0]=np.roll(a[:,:,0],dx,1); a[:,:,2]=np.roll(a[:,:,2],-dx,1); return a
    if typ=='slice':
        rng=np.random.RandomState(seed); a=a.copy(); y=0
        while y<H:
            hh=int(rng.randint(40,160)); sh=int(rng.randint(-170,170)*p); a[y:y+hh]=np.roll(a[y:y+hh],sh,1); y+=hh
        dx=int(22*p); a[:,:,0]=np.roll(a[:,:,0],dx,1); a[:,:,2]=np.roll(a[:,:,2],-dx,1); return a
    if typ=='flash':
        a=rzoom(a,1+0.18*p,3).astype(np.float32); a=a*(1-0.9*p)+255*0.9*p; return np.clip(a,0,255).astype(np.uint8)
    if typ=='color':
        rng=np.random.RandomState(seed//3); c1=np.array(PAL[rng.randint(5)],np.float32); c2=np.array(PAL[rng.randint(5)],np.float32)
        gx=np.linspace(0,1,W,dtype=np.float32)[None,:,None]; gy=np.linspace(0,1,H,dtype=np.float32)[:,None,None]
        g=c1*(1-(gx*0.6+gy*0.4))+c2*(gx*0.6+gy*0.4)
        af=a.astype(np.float32)/255; gf=np.clip(g,0,255)/255*min(1,p*1.1)
        out=1-(1-af)*(1-gf); a=(out*255).astype(np.uint8)
        return rzoom(a,1+0.12*p,3)
    if typ=='kaleido':
        h2=W//2; L=a[:,:h2]; m=np.concatenate([L,L[:,::-1]],1)
        mt=a.copy(); sc=np.linspace(1.0,0.0,H,dtype=np.float32)
        m2=cv2.addWeighted(a,1-min(1,p*1.6),m,min(1,p*1.6),0)
        return rzoom(m2,1+0.15*p,3)
    if typ=='mirror':
        top=a[:H//2]; m=np.concatenate([top,top[::-1]],0)
        return cv2.addWeighted(a,1-min(1,p*1.6),m,min(1,p*1.6),0)
    if typ=='blinds':
        rng=np.random.RandomState(seed); a=a.copy(); nb=14; bh=H//nb
        for q in range(nb):
            y0=q*bh; y1=H if q==nb-1 else y0+bh
            if q%2==0: a[y0:y1]=np.roll(a[y0:y1],int(W*0.5*p*(1 if q%4==0 else -1)),1)
            elif rng.rand()<p*0.8: a[y0:y1]=a[y0:y1]*0.1
        return a
    if typ=='invert':
        q=min(1,p*1.8); inv=255-a; g=cv2.cvtColor(inv,cv2.COLOR_BGR2GRAY); g=cv2.cvtColor(g,cv2.COLOR_GRAY2BGR)
        return cv2.addWeighted(a,1-q,g,q,0)
    return a

A0=5.64; B=0.521
def T(k): return A0+B*k
FIN=T(29)
SRC='/home/claude/rap/b.mp4'
cap=cv2.VideoCapture(SRC); SF=30
# (t0,t1,start,cx,speed)
INTRO=[(0,1.41,30.2,.55),(1.41,2.82,17.5,.6),(2.82,4.23,12.0,.6),(4.23,A0,15.0,.5)]
RAW=[(0,1,22.0,.68),(1,1,83.0,.72),(2,1,64.3,.35),(3,1,30.4,.55),(4,2,218.6,.5),(6,1,79.5,.3),(7,1,167.0,.4),
 (8,1,204.2,.35),(9,1,206.3,.65),(10,1,225.0,.5),(11,1,171.0,.5),(12,1,188.2,.75),(13,1,202.0,.6),(14,1,52.6,.5),
 (15,1,222.6,.55),(16,1,209.0,.55),(17,1,220.5,.4),(18,1,40.0,.4),(19,1,227.3,.6),(20,1,196.5,.5),(21,1,183.5,.6),
 (22,2,298.0,.5),(24,1,108.5,.5),(25,1,27.5,.35),(26,1,57.0,.6),(27,1,80.8,.3),(28,1,302.5,.5)]
EFF=['flash','color','whip_l','kaleido','zoom','color','rgb','spin','color','whip_r','zoom','blinds','color','rgb','flash','color','whip_l','zoom','color','kaleido','spin','color','rgb','whip_r','color','zoom','flash','color','rgb']
CL=[]
for j,(a,b,st,cx) in enumerate(INTRO):
    CL.append(dict(t0=a,t1=b,st=st,cx=cx,sp=0.6,eff='color' if j%2 else 'rgb'))
for i,(k,nb,st,cx) in enumerate(RAW):
    CL.append(dict(t0=T(k),t1=T(k+nb),st=st,cx=cx,sp=0.5 if nb==2 else 1.0,eff=EFF[i%len(EFF)]))
for i,c in enumerate(CL): c['i']=i
def crop0(f,cx):
    h,w=f.shape[:2]; cw=h*9/16; cxp=min(max(cx*w,cw/2),w-cw/2); x0=int(round(cxp-cw/2))
    return f[:, x0:x0+int(round(cw))].copy()
def zoomed(c,z,fy=0.4):
    h,w=c.shape[:2]
    if z>1:
        ch=h/z; cwid=w/z; y0=int(round((h-ch)*fy)); x0=int(round((w-cwid)/2)); c=c[y0:y0+int(round(ch)),x0:x0+int(round(cwid))]
    o=cv2.resize(c,(1080,1920),interpolation=cv2.INTER_CUBIC)
    bl=cv2.GaussianBlur(o,(0,0),3); return cv2.addWeighted(o,1.5,bl,-0.5,0)
cache={}
def clip_frames(c):
    i=c['i']
    if i in cache: return cache[i]
    cache.clear()
    dur=c['t1']-c['t0']; n=int(dur*c['sp']*SF)+6
    cap.set(cv2.CAP_PROP_POS_MSEC,c['st']*1000); fr=[]
    for _ in range(n):
        ok,f=cap.read()
        if not ok: break
        fr.append(crop0(f,c['cx']))
    if not fr: fr=[np.zeros((1080,608,3),np.uint8)]
    cache[i]=fr; return fr
def cut_idx(t):
    for j,c in enumerate(CL):
        if t<c['t1']-1e-6: return j
    return len(CL)-1
def vit(a):
    hsv=cv2.cvtColor(a,cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:,:,1]=np.clip(hsv[:,:,1]*1.38,0,255); hsv[:,:,2]=np.clip(hsv[:,:,2]*1.12+8,0,255)
    o=cv2.cvtColor(hsv.astype(np.uint8),cv2.COLOR_HSV2BGR).astype(np.float32)
    bl=cv2.GaussianBlur(o,(0,0),22); o=1-(1-o/255)*(1-bl/255*0.35); o=o*255
    # pastel pink/cyan tint
    yy=np.linspace(0,1,H,dtype=np.float32)[:,None,None]
    tint=np.array([200,120,255],np.float32)*(1-yy)+np.array([255,220,120],np.float32)*yy
    o=o*0.9+tint*0.10
    return np.clip(o,0,255).astype(np.uint8)
MG=(255,60,170)
def card(t):
    img=Image.new('RGB',(W,H)); d=ImageDraw.Draw(img)
    g=np.zeros((H,W,3),np.uint8); yy=np.linspace(0,1,H)[:,None]
    g[:,:,0]=(255*(1-yy)+120*yy); g[:,:,1]=(90*(1-yy)+220*yy); g[:,:,2]=(190*(1-yy)+255*yy)
    img=Image.fromarray(g); 
    slamtxt(img,t,FIN,'ИИ-ЭДИТЫ',820,200,WH,10,(120,30,160))
    slamtxt(img,t,FIN+0.25,'@claude.edits2',1060,84,WH,6,(120,30,160),FM)
    return np.asarray(img)[:,:,::-1].copy()
def render(i):
    t=i/FPS
    if t<FIN:
        ci=cut_idx(t); c=CL[ci]; lt=max(0,t-c['t0']); fr=clip_frames(c)
        idx=min(len(fr)-1,int(lt*c['sp']*SF)); dur=c['t1']-c['t0']
        a=zoomed(fr[idx],1.0+0.10*min(1,lt/max(0.4,dur)))
        a=vit(a)
        if t>=A0:
            bt=(t-A0)/B; ts=(bt-math.floor(bt))*B
            z=1+(0.075 if int(bt)%4==0 else 0.045)*math.exp(-ts/0.11)
            M=np.float32([[z,0,W/2*(1-z)],[0,z,H/2*(1-z)]]); a=cv2.warpAffine(a,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
        pp=(1-(t-c['t0'])/0.22)
        if pp>0 and ci>0: a=fx(a,c['eff'],'post',pp*pp,i)
        if ci+1<len(CL):
            tn=c['t1']-t; pr=1-tn/0.09
            if pr>0: a=fx(a,CL[ci+1]['eff'],'pre',pr,i)
        im=Image.fromarray(a[:,:,::-1])
        if t<A0:
            slamtxt(im,t,0.2,'РАПУНЦЕЛЬ',1560,170,WH,10,MG)
            if t>=2.82: slamtxt(im,t,2.82,'ВИТАМИНКА',1560,150,WH,10,(40,170,255))
            if t>=3.3: emopop(im,t,3.3,'🌈',880,1380,190)
        a=np.asarray(im)[:,:,::-1].copy()
    else:
        a=card(t)
    a=a.astype(np.float32)
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    v=1-0.18*(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2)/2
    a=a*v[:,:,None]
    a+=np.random.RandomState(i).randn(H,W,1).astype(np.float32)*3
    a=np.clip(a,0,255).astype(np.uint8)
    f=min(1,(DUR-t)/0.4)
    if f<1: a=(a*max(0,f)).astype(np.uint8)
    return a
if PREVIEW:
    times=[0.3,1.0,2.0,3.0,3.6,5.0,5.7,6.0]+[c['t0']+0.25*(c['t1']-c['t0']) for c in CL[4:]]+[FIN+0.9]
    tiles=[cv2.resize(render(int(x*FPS)),(180,320)) for x in times]
    cols=10; rows=(len(tiles)+cols-1)//cols
    sheet=np.zeros((rows*320,cols*180,3),np.uint8)
    for n,tt in enumerate(tiles):
        r,c=divmod(n,cols); sheet[r*320:(r+1)*320,c*180:(c+1)*180]=tt
    cv2.imwrite(OUT,sheet); sys.exit()
FC="[1:a]volume=1.0,afade=t=out:st=21.5:d=0.78[aout]"
cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
     '-i',AUD,'-filter_complex',FC,'-map','0:v','-map','[aout]','-t',str(DUR),
     '-c:v','libx264','-preset','medium','-crf','22','-maxrate','10M','-bufsize','20M','-pix_fmt','yuv420p',
     '-c:a','aac','-b:a','192k','-movflags','+faststart',OUT]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for i in range(N): p.stdin.write(render(i).tobytes())
p.stdin.close(); p.wait()
