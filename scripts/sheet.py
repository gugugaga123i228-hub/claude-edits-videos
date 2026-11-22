import subprocess,os,sys
from PIL import Image,ImageDraw
f,dur=sys.argv[1],float(sys.argv[2])
c=[0]+[float(l.split('pts_time:')[1].split()[0]) for l in open(f'sc_{f}.log') if 'pts_time:' in l]+[dur]
sc=[(c[i],c[i+1]) for i in range(len(c)-1) if c[i+1]-c[i]>=0.8]
os.makedirs(f'th_{f}',exist_ok=True); tiles=[]
for i,(s,e) in enumerate(sc):
    t=s+min(0.4,(e-s)/2); p=f'th_{f}/{i:03d}.jpg'
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',f'{f}.mp4','-frames:v','1','-vf','scale=200:-1',p]); tiles.append((i,s,e,Image.open(p)))
cols=8;w,h=200,113;rows=(len(tiles)+cols-1)//cols
im=Image.new('RGB',(cols*w,rows*h));d=ImageDraw.Draw(im)
for n,(i,s,e,x) in enumerate(tiles):
    im.paste(x.resize((w,h)),((n%cols)*w,(n//cols)*h)); d.rectangle(((n%cols)*w,(n//cols)*h,(n%cols)*w+95,(n//cols)*h+12),fill=(0,0,0)); d.text(((n%cols)*w+2,(n//cols)*h),f'{s:.1f}-{e:.1f}',fill=(255,255,0))
im.save(f'sheet_{f}.jpg'); print(f,len(sc),im.size)
