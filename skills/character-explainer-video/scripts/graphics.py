"""Portable illustrated primitives extracted from the accepted film. Pillow only."""
import math
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

W,H,FPS=1920,1080,24
FONT=None; BOLD_INDEX=0; REGULAR_INDEX=0
INK='#344B43'; MUTED='#6E7D72'; CREAM='#FFF8ED'; MINT='#D9E9D0'; GREEN='#729779'; PEACH='#F4C6AA'; PINK='#EBA8A3'; GOLD='#EDC96D'; BLUE='#BEDCE6'; LILAC='#D9D0E9'; PAPER='#FFFEF8'

@lru_cache(None)
def ft(n,b=True): return ImageFont.truetype(FONT,int(n),index=BOLD_INDEX if b else REGULAR_INDEX)
def text(d,xy,s,n=36,c=INK,anchor=None,b=True):
 d.text(xy,str(s).replace('−','-').replace('±','+/-'),font=ft(n,b),fill=c,anchor=anchor)
def center(d,x,y,s,n=36,c=INK,b=True): text(d,(x,y),s,n,c,'mm',b)
def ease(x): x=max(0,min(1,x));return x*x*(3-2*x)
def step(t,a,b): return ease((t-a)/max(.01,b-a))
def mix(a,b,p):return a+(b-a)*p
def rr(d,box,fill=PAPER,r=24,outline=None,width=3):d.rounded_rectangle(tuple(int(x) for x in box),radius=r,fill=fill,outline=outline,width=width)
def pill(d,x,y,label,col=MINT,n=27):
 width=d.textlength(label,font=ft(n))+42;rr(d,(x,y,x+width,y+48),col,24);center(d,x+width/2,y+24,label,n);return width
def arrow(d,a,b,color=GREEN,w=8,dashed=False):
 dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy)
 if length<1:return
 ux,uy=dx/length,dy/length
 if dashed:
  for k in range(0,int(length)-22,27):
   end=min(k+13,length-22);d.line((a[0]+ux*k,a[1]+uy*k,a[0]+ux*end,a[1]+uy*end),fill=color,width=w)
 else:d.line((*a,*b),fill=color,width=w)
 d.polygon([b,(b[0]-22*ux+11*uy,b[1]-22*uy-11*ux),(b[0]-22*ux-11*uy,b[1]-22*uy+11*ux)],fill=color)
def check(d,x,y,color=GREEN,size=28):d.line((x-size*.5,y,x-size*.08,y+size*.4,x+size*.65,y-size*.5),fill=color,width=max(4,int(size*.16)),joint='curve')

@lru_cache(None)
def icon(kind,size=180,color=MINT):
 im=Image.new('RGBA',(260,260));d=ImageDraw.Draw(im)
 stroke=INK
 if kind=='box':
  d.polygon([(38,78),(128,33),(222,78),(128,127)],fill='#F5D99D',outline=stroke,width=5)
  d.polygon([(38,78),(128,127),(128,228),(38,179)],fill='#EBC281',outline=stroke,width=5)
  d.polygon([(128,127),(222,78),(222,179),(128,228)],fill='#DDA96B',outline=stroke,width=5)
  d.polygon([(78,58),(168,104),(192,92),(101,47)],fill='#FFF0CA')
  rr(d,(149,143,198,177),PAPER,5);d.line((159,154,189,154),fill='#AE9572',width=3)
 elif kind in ['shop','supplier','bank','company']:
  rr(d,(37,91,223,224),color,14,stroke,5)
  if kind=='supplier':
   d.polygon([(37,100),(37,60),(96,89),(96,60),(155,89),(155,60),(223,95)],fill=color,outline=stroke,width=5)
   rr(d,(188,26,215,90),PEACH,4,stroke,5)
  elif kind=='bank':
   d.polygon([(23,88),(130,24),(238,88)],fill=PEACH,outline=stroke,width=5)
   for x in [65,117,169]:rr(d,(x,106,x+25,207),PAPER,5)
   center(d,130,64,'₩',35)
  else:
   rr(d,(23,63,237,111),PEACH if kind=='shop' else GREEN,12,stroke,5)
   if kind=='shop':
    for x in [25,68,111,154,197]:d.rectangle((x,66,x+20,108),fill=PAPER)
   else:center(d,130,87,'기업',30,PAPER)
  if kind!='bank':
   rr(d,(60,131,105,174),PAPER,6,stroke,3);rr(d,(151,133,197,224),PAPER,8,stroke,3)
 elif kind in ['receipt','contract','ledger']:
  rr(d,(51,24,208,236),PAPER,13,stroke,5)
  rr(d,(72,46,185,79),color,8)
  for y in [103,132,161]:d.line((77,y,181,y),fill='#9BAC9C',width=5)
  if kind=='contract':check(d,157,199,GREEN,31)
  elif kind=='ledger':
   d.line((120,91,120,215),fill=GREEN,width=4);d.line((70,185,190,185),fill=GREEN,width=4)
  else:center(d,130,205,'₩',35,GREEN)
 elif kind=='calendar':
  rr(d,(32,47,227,230),PAPER,20,stroke,5);rr(d,(32,47,227,100),color,18)
  for x in [75,180]:d.line((x,28,x,68),fill=stroke,width=10)
  for y in range(128,205,35):
   for x in range(62,205,35):rr(d,(x,y,x+17,y+17),MINT,4)
  d.ellipse((126,156,156,187),fill=PEACH)
 elif kind in ['tv','online']:
  rr(d,(23,57,237,204),color,19,stroke,5);rr(d,(40,76,218,183),PAPER,12)
  if kind=='tv':
   d.line((96,30,129,57,169,23),fill=stroke,width=5)
   d.polygon([(111,105),(111,157),(153,131)],fill=PINK)
  else:
   d.line((45,100,212,100),fill=stroke,width=3)
   for x in [57,71,85]:d.ellipse((x,84,x+6,90),fill=PINK)
   d.line((82,120,95,153,158,153,172,119,95,119),fill=GREEN,width=6)
   for x in [107,149]:d.ellipse((x,164,x+8,172),fill=GREEN)
  d.line((105,207,98,230,165,230,157,207),fill=stroke,width=5)
 elif kind=='phone':
  rr(d,(68,25,194,237),color,22,stroke,5);rr(d,(82,51,180,202),PAPER,11)
  center(d,131,127,'☎',70,GREEN);d.ellipse((124,213,138,226),fill=stroke)
 elif kind=='coin':
  d.ellipse((32,30,230,228),fill=GOLD,outline='#C79F50',width=6)
  d.ellipse((48,46,214,212),outline='#FFF0B9',width=7);center(d,131,133,'₩',105,'#9C7635')
 elif kind=='truck':
  rr(d,(23,73,153,186),color,10,stroke,5);d.polygon([(153,113),(204,113),(238,147),(238,186),(153,186)],fill=PEACH,outline=stroke,width=5)
  rr(d,(169,125,200,150),PAPER,4)
  for x in [65,196]:d.ellipse((x-22,168,x+22,212),fill=stroke);d.ellipse((x-10,180,x+10,200),fill=PAPER)
 elif kind=='calculator':
  rr(d,(55,22,207,239),color,19,stroke,5);rr(d,(74,43,189,91),PAPER,9)
  for y in [115,157,199]:
   for x in [78,119,160]:rr(d,(x,y,x+26,y+23),PEACH if x==160 else PAPER,5)
 elif kind=='lock':
  d.arc((75,34,187,171),180,360,fill=stroke,width=15);rr(d,(49,111,211,232),GOLD,24,stroke,5);d.ellipse((116,151,144,179),fill=stroke);d.line((130,172,130,199),fill=stroke,width=9)
 elif kind=='check':
  d.ellipse((30,30,230,230),fill=MINT);check(d,130,130,GREEN,110)
 else:raise ValueError(kind)
 return im.resize((size,size),Image.Resampling.LANCZOS)
