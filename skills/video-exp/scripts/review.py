"""Make local motion contact sheets. No generation."""
import argparse,io,math,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
from media_contract import probe
p=argparse.ArgumentParser(description=__doc__);p.add_argument('video');p.add_argument('output');p.add_argument('--step',type=float,default=1);a=p.parse_args()
if a.step<=0:p.error('step must be positive')
if Path(a.output).exists():raise FileExistsError(a.output)
duration=float(probe(a.video)['format']['duration']);times=[k*a.step for k in range(math.ceil(duration/a.step)) if k*a.step<duration-.05]
im=Image.new('RGB',(1280,210*math.ceil(len(times)/4)),'#fff8ed');d=ImageDraw.Draw(im)
for j,t in enumerate(times):
 raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',a.video,'-frames:v','1','-vf','scale=320:180','-f','image2pipe','-vcodec','mjpeg','pipe:1'])
 x=j%4*320;y=j//4*210;im.paste(Image.open(io.BytesIO(raw)),(x,y));d.text((x+7,y+185),f'{t:.2f}s',fill='black')
im.save(a.output)
