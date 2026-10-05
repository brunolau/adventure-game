from PIL import Image, ImageDraw, ImageFont
import os
A='build/screens/m3/all'
try: F=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',28)
except: F=ImageFont.load_default()
def tile(rid,w,h,suffix='_00'):
    p=f'{A}/{rid}{suffix}.png'
    im=Image.open(p).convert('RGB').resize((w,h),Image.LANCZOS)
    return im
# contact sheets 2x2 for S01..S39
ids=[f'S{i:02d}' for i in range(1,40)]
for k in range(0,len(ids),4):
    grp=ids[k:k+4]; sh=Image.new('RGB',(1920,1080),'black')
    for j,r in enumerate(grp):
        t=tile(r,960,540); d=ImageDraw.Draw(t); d.rectangle([0,0,90,36],fill='black'); d.text((6,2),r,font=F,fill='yellow')
        sh.paste(t,((j%2)*960,(j//2)*540))
    sh.save(f'build/m3logs/sheets/sheet_{grp[0]}.jpg',quality=88)
fam={'L_STOP':[('S57',1982),('S11',1995),('S51',2020)],'L_SCHOOL_FRONT':[('S58',1982),('S12',1995),('S52',2020)],
 'L_HALL':[('S59',1982),('S13',1995),('S53',2020)],'L_CLASS':[('S60',1982),('S14',1995)],
 'L_CABINET':[('S63',1982),('S15',1995),('S54',2020)],'L_YARD':[('S61',1982),('S17',1995),('S55',2020)],'L_WINDOW':[('S64',1982),('S56',2020)]}
import json
for f,rooms in fam.items():
    n=len(rooms); W=960; H=540
    sh=Image.new('RGB',(W*n,H+90),(20,20,20)); d=ImageDraw.Draw(sh)
    anchors=None
    for j,(r,y) in enumerate(rooms):
        t=tile(r,W,H); sh.paste(t,(j*W,90))
        b=json.load(open(f'src/game/data/blocking/{r}.json',encoding='utf-8'))
        a=b.get('anchors',{}); dd=ImageDraw.Draw(sh)
        for name,(x,yy) in a.items():
            cx,cy=j*W+x/2,90+yy/2; dd.ellipse([cx-7,cy-7,cx+7,cy+7],outline='red',width=3); dd.text((cx+9,cy-12),name,font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16),fill='red')
        d.text((j*W+10,50),f'{r}  {y}   walk_band {b.get("walk_band")} scale {b.get("actor_scale")}',font=F,fill='white')
    d.text((10,8),f+'  (in-engine, natural blocking; red = landmark_layouts anchors from the blocking files)',font=F,fill='yellow')
    sh.save(f'docs/families/{f}.png')
print('ok')
