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






import re, os
SNAP='/home/claude/iron/snap.mp4'; CWV='/home/claude/iron/cw.mp4'; SADV='/home/claude/iron/sad.mp4'
M5V='/home/claude/iron/m5.mp4'; M42V='/home/claude/iron/m42.mp4'
A0=7.4; B=0.5768
def T(k): return A0+B*k
FIN=T(31)
def scenes(name):
    p=f'/home/claude/iron/sc_{name}.log'
    if not os.path.exists(p): return []
    return sorted(float(m) for m in re.findall(r'pts_time:([0-9.]+)',open(p).read()))
SC={'cw':scenes('cw'),'sad':scenes('sad'),'m5':scenes('m5'),'m42':[]}
def snapst(srcn,st,need):
    cuts=[0.0]+SC[srcn]+[1e9]
    for a,b in zip(cuts,cuts[1:]):
        if a<=st<b:
            if st+need+0.08>b: st=max(a+0.05,b-need-0.08)
            elif st<a+0.05: st=a+0.05
            return st
    return st
EFF=['flash','color','whip_l','kaleido','zoom','blinds','rgb','invert','spin','slice','color','whip_r','mirror','zoom','blinds','color']
RAW=[(0,1,'cw',240.0,.5,1),(1,1,'m5',8.4,.45,1),(2,1,'cw',176.0,.45,1),(3,1,'m5',19.2,.5,1),
 (4,2,'cw',229.5,.35,.5),(6,1,'m42',144.0,.5,1),(7,1,'cw',195.5,.55,1),(8,1,'m5',24.5,.5,1),
 (9,1,'cw',220.5,.5,1),(10,1,'sad',9.0,.5,1),(11,1,'cw',190.5,.5,1),(12,2,'m5',4.2,.5,.5),
 (14,1,'cw',235.5,.5,1),(15,1,'m42',156.0,.5,1),(16,1,'cw',185.5,.5,1),(17,1,'m5',10.0,.6,1),
 (18,1,'cw',225.5,.5,1),(19,1,'sad',3.5,.5,1),(20,1,'cw',245.5,.5,1),(21,1,'m42',182.0,.5,1),
 (22,1,'cw',230.5,.4,1),(23,1,'m5',20.0,.5,1),(24,2,'sad',225.5,.6,.5),(26,1,'cw',215.5,.5,1),
 (27,1,'m5',25.0,.5,1),(28,1,'cw',241.5,.5,1),(29,1,'cw',180.5,.42,1),(30,1,'cw',244.5,.5,1)]
CL=[]
for i,(k,nb,sn,st,cx,sp) in enumerate(RAW):
    need=nb*B*sp+0.1
    CL.append(dict(t0=T(k),t1=T(k+nb),src=sn,st=snapst(sn,st,need),cx=cx,sp=sp,eff=EFF[i%len(EFF)],i=i))
FPSMAP={'cw':60,'sad':60,'m5':23.976,'m42':23.976}
caps={'snap':cv2.VideoCapture(SNAP),'cw':cv2.VideoCapture(CWV),'sad':cv2.VideoCapture(SADV),'m5':cv2.VideoCapture(M5V),'m42':cv2.VideoCapture(M42V)}
def crop0(f,cx):
    h,w=f.shape[:2]; cw=h*9/16; cxp=min(max(cx*w,cw/2),w-cw/2); x0=int(round(cxp-cw/2))
    return f[:, x0:x0+int(round(cw))].copy()
def zoomed(c,z,fy=0.5):
    h,w=c.shape[:2]
    if z>1:
        ch=h/z; cwid=w/z; y0=int(round((h-ch)*fy)); x0=int(round((w-cwid)/2)); c=c[y0:y0+int(round(ch)),x0:x0+int(round(cwid))]
    o=cv2.resize(c,(1080,1920),interpolation=cv2.INTER_CUBIC)
    bl=cv2.GaussianBlur(o,(0,0),3); return cv2.addWeighted(o,1.5,bl,-0.5,0)
def load(cap,st,dur,fps,cx):
    cap.set(cv2.CAP_PROP_POS_MSEC,st*1000); n=int(dur*fps)+3; out=[]
    for _ in range(n):
        ok,f=cap.read()
        if not ok: break
        out.append(crop0(f,cx))
    return out
INTRO=None
def intro_frames():
    global INTRO
    if INTRO is None:
        INTRO=(load(caps['snap'],17.97,5.35,24,.62),load(caps['snap'],28.45,1.15,24,.60))
    return INTRO
cache={}
def clip_frames(c):
    i=c['i']
    if i in cache: return cache[i]
    cache.clear()
    cap=caps[c['src']]; fps=FPSMAP[c['src']]; dur=c['t1']-c['t0']; n=int(dur*c['sp']*fps)+8
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
def rzoom(a,s,n=5):
    acc=np.zeros(a.shape,np.float32)
    for q in range(n):
        si=1+(s-1)*q/(n-1); M=np.float32([[si,0,W/2*(1-si)],[0,si,H/2*(1-si)]])
        acc+=cv2.warpAffine(a,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
    return (acc/n).astype(np.uint8)
PAL=[(0,200,255),(255,220,0),(160,60,255),(120,255,90),(255,90,40)]
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
def card(t):
    img=Image.new('RGB',(W,H)); d=ImageDraw.Draw(img)
    d.rectangle([0,0,W,H],fill=(8,8,8)); radial(d,W/2,900,(44,30,12),t)
    slamtxt(img,t,FIN,'ИИ-ЭДИТЫ',820,200,WH,0)
    slamtxt(img,t,FIN+0.3,'@claude.edits2',1060,84,(235,235,240),0,BK,FM)
    return np.asarray(img)[:,:,::-1].copy()
def radial(d,cx,cy,col,ts,n=28):
    Rr=2400
    for k in range(n):
        a0=(k/n+ts*0.08)*2*math.pi; a1=a0+math.pi/n*0.55
        d.polygon([(cx,cy),(cx+Rr*math.cos(a0),cy+Rr*math.sin(a0)),(cx+Rr*math.cos(a1),cy+Rr*math.sin(a1))],fill=col)
PRE=['rgb','color','slice','kaleido','color','rgb']
def render(i):
    t=i/FPS
    if t<A0:
        f1,f2=intro_frames()
        if t<1.0:
            a=zoomed(f1[0],1.0+0.06*t,0.35)
            ph=t/1.0; st=int(t*7)  # 7 quick glitch bursts
            local=(t*7)%1.0; p=max(0,1-local*2.2)*(0.5+0.5*ph)
            a=fx(a,PRE[st%len(PRE)],'post',p,i)
            ts=1.0
        elif t<6.3:
            u=t-1.0; q=u/5.3; z=1.06+0.2*(q**1.2); fr=f1[min(len(f1)-1,int(u*24))]; a=zoomed(fr,z,0.35)
            if u>5.18: a=fx(a,'rgb','pre',(u-5.18)/0.12,i)
            ts=1.0
        else:
            u=t-6.3; fr=f2[min(len(f2)-1,int(u*24))]; z=1+0.6*(u/1.1)**1.5; a=zoomed(fr,z,0.35)
            if u<0.14: a=fx(a,'rgb','post',1-u/0.14,i)
            sh=int(14*(u/1.1)); a=np.roll(a,(i*7)%(2*sh+1)-sh if sh else 0,0)
            ts=1.0
    elif t<FIN:
        ci=cut_idx(t); c=CL[ci]; lt=max(0,t-c['t0']); fr=clip_frames(c)
        idx=min(len(fr)-1,int(lt*c['sp']*FPSMAP[c['src']])); dur=c['t1']-c['t0']
        a=zoomed(fr[idx],1.0+0.10*min(1,lt/max(0.4,dur)),0.4)
        bt=(t-A0)/B; ts=(bt-math.floor(bt))*B
        z=1+(0.075 if int(bt)%4==0 else 0.045)*math.exp(-ts/0.11)
        M=np.float32([[z,0,W/2*(1-z)],[0,z,H/2*(1-z)]]); a=cv2.warpAffine(a,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
        pp=(1-(t-c['t0'])/0.22)
        if pp>0: a=fx(a,c['eff'],'post',pp*pp,i)
        if ci+1<len(CL):
            tn=c['t1']-t; pr=1-tn/0.09
            if pr>0: a=fx(a,CL[ci+1]['eff'],'pre',pr,i)
        a=a.astype(np.float32); a[:,:,2]*=1.10; a[:,:,0]*=0.90; a=np.clip(a,0,255).astype(np.uint8)
    else:
        a=card(t); ts=t-FIN
    a=a.astype(np.float32)
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    v=1-0.3*(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2)/2
    a=a*v[:,:,None]; a=(a-128)*1.1+128
    a+=np.random.RandomState(i).randn(H,W,1).astype(np.float32)*4
    a=np.clip(a,0,255).astype(np.uint8)
    f=min(1,(DUR-t)/0.4)
    if f<1: a=(a*max(0,f)).astype(np.uint8)
    return a
if PREVIEW:
    times=[0.15,0.5,0.85,1.5,4.0,6.0,6.4,7.0,7.45]+[c['t0']+min(0.2,(c['t1']-c['t0'])*0.5) for c in CL]+[c['t0']+0.05 for c in CL[:12]]+[FIN+0.9]
    tiles=[cv2.resize(render(int(x*FPS)),(180,320)) for x in times]
    cols=10; rows=(len(tiles)+cols-1)//cols
    sheet=np.zeros((rows*320,cols*180,3),np.uint8)
    for n,tt in enumerate(tiles):
        r,c=divmod(n,cols); sheet[r*320:(r+1)*320,c*180:(c+1)*180]=tt
    cv2.imwrite(OUT,sheet); sys.exit()
SONG="/mnt/user-data/uploads/ba181880-7656751952572450832uasaverbot.m4a"
FC=("[1:a]atrim=17.9:23.1,asetpts=PTS-STARTPTS,afade=t=out:st=5.1:d=0.15,adelay=1000|1000[a1];"
    "[1:a]atrim=28.45:29.55,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.03,afade=t=out:st=1.0:d=0.1,adelay=6300|6300[a2];"
    "[a1][a2]amix=inputs=2:duration=longest:normalize=0,volume=4.0,alimiter=limit=0.9:attack=3:release=50[ia];"
    "[2:a]atrim=4.24:31.3,asetpts=PTS-STARTPTS,volume='if(lt(t,7.35),0.18,0.95)':eval=frame[sg];"
    "[ia][sg]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95,afade=t=out:st=26.3:d=0.7[aout]")
cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
     '-i',SNAP,'-i',SONG,'-filter_complex',FC,'-map','0:v','-map','[aout]','-t',str(DUR),
     '-c:v','libx264','-preset','medium','-crf','23','-maxrate','10M','-bufsize','20M','-pix_fmt','yuv420p',
     '-c:a','aac','-b:a','192k','-movflags','+faststart',OUT]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for i in range(N): p.stdin.write(render(i).tobytes())
p.stdin.close(); p.wait()
