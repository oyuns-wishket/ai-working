"""Render an explicit film manifest. Local files only; no generation or network calls."""
import argparse, json, math, subprocess, wave
from pathlib import Path
from PIL import Image, ImageDraw
import graphics as g

W,H,FPS,VW,VH=1920,1080,24,1480,832

from media_contract import probe, resolve, validate, render_receipt, file_hash

def wrap(text,width,size):
    d=ImageDraw.Draw(Image.new('RGB',(1,1)));out=[]
    for para in text.split('\n'):
        line=''
        for ch in para:
            if line and d.textlength(line+ch,font=g.ft(size,False))>width:out.append(line);line=ch
            else:line+=ch
        if line:out.append(line)
    return out

def block(d,text,x,y,width=330,size=32,color=g.INK):
    for line in wrap(text,width,size):g.text(d,(x,y),line,size,color);y+=size+11
    return y

def frame(raw,data,s,cut,t):
    im=Image.new('RGBA',(W,H),g.CREAM);d=ImageDraw.Draw(im)
    g.text(d,(30,18),data['title'],22,g.GREEN)
    size=42
    while d.textlength(s['title'],font=g.ft(size))>1470 and size>24:size-=1
    g.text(d,(30,53),s['title'],size);g.pill(d,1560,26,s['chapter'],g.MINT,24)
    im.paste(Image.frombytes('RGB',(VW,VH),raw),(20,124))
    g.rr(d,(1518,126,1898,955),g.PAPER,26)
    g.text(d,(1542,149),data.get('panel_heading','고양이가 하는 일'),23,g.GREEN)
    im.alpha_composite(g.icon(cut.get('icon','receipt'),100),(1658,201))
    y=block(d,cut['action'],1542,330,size=35)
    meaning_bottom=block(d,cut.get('meaning',''),1542,y+14,size=26,color=g.MUTED)
    if meaning_bottom>530:raise ValueError('Action/meaning exceeds its slot')
    for e in s.get('panels',[]):
        if e['start']<=t<e['end']:
            if e.get('y',550)<max(530,meaning_bottom):raise ValueError('Panel overlaps meaning')
            bottom=block(d,e['text'],1542,e.get('y',550),size=e.get('size',32),color=e.get('color',g.INK))
            if bottom>(830 if s.get('status') else 900):raise ValueError('Panel text overlaps status/footer; shorten or reduce size')
    if s.get('status') and block(d,s['status'],1542,842,size=23,color='#9B5944')>910:raise ValueError('Status overlaps footer')
    if s.get('footnote') and block(d,s['footnote'],1542,915,size=20,color=g.MUTED)>950:raise ValueError('Footnote exceeds panel')
    for e in s.get('props',[]):
        if e['start']<=t<e['end']:
            x,y=e['xy']; target=e.get('to',e['xy'])
            q=g.step(t,e['start'],e.get('arrive',e['end']))
            g.pill(d,int(g.mix(x,target[0],q)),int(g.mix(y,target[1],q)),e['text'],e.get('color',g.MINT),e.get('size',24))
    g.rr(d,(36,902,690,946),(255,254,248,235),17);g.text(d,(55,911),cut['action'],26)
    lead=data.get('audio_lead',.25)
    for c in s.get('captions',[]):
        a,b=c['start']+lead,c['end']+lead
        if a<=t<b:
            lines=wrap(c['text'],1770,35)
            if len(lines)>2:
                k=min((len(lines)-1)//2,int((t-a)/max(.1,b-a)*math.ceil(len(lines)/2)));lines=lines[k*2:k*2+2]
            g.rr(d,(24,972,1896,1067),g.INK,22);yy=995 if len(lines)>1 else 1020
            for line in lines:g.center(d,960,yy,line,35,g.PAPER,False);yy+=40
            break
    return im.convert('RGB')

def read_exact(pipe,n):
    result=bytearray()
    while len(result)<n:
        part=pipe.read(n-len(result))
        if not part:break
        result.extend(part)
    if len(result)!=n:raise RuntimeError('Source ended early; no freeze/loop fallback')
    return bytes(result)

def render_scene(data,root,out,i):
    s=data['scenes'][i];dest=out/f'scene_{i:03}.mp4'
    if dest.exists():raise FileExistsError(dest)
    delay=round(data.get('audio_lead',.25)*1000)
    cmd=['ffmpeg','-v','error','-n','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(resolve(root,s['audio'])),'-af',f'adelay={delay}:all=1,apad,loudnorm=I=-17:TP=-1.5:LRA=9','-c:v','libx264','-preset','veryfast','-crf','20','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-ar','48000','-t',str(s['frames']/FPS),'-movflags','+faststart',str(dest)]
    enc=subprocess.Popen(cmd,stdin=subprocess.PIPE);cursor=0
    try:
        for j,c in enumerate(s['cuts']):
            vf=f'scale={VW}:{VH}:force_original_aspect_ratio=decrease,pad={VW}:{VH}:(ow-iw)/2:(oh-ih)/2:color=0xFFF8ED,fps={FPS}'
            dec=subprocess.Popen(['ffmpeg','-v','error','-threads','2','-ss',str(c.get('source_in',0)),'-i',str(resolve(root,c['video'])),'-vf',vf,'-frames:v',str(c['frames']),'-an','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
            try:
                for f in range(c['frames']):
                    im=frame(read_exact(dec.stdout,VW*VH*3),data,s,c,(cursor+f)/FPS)
                    if f in [0,min(96,c['frames']-1),c['frames']-1]:im.save(out/f'preview_{i:03}_{j}_{f:03}.jpg',quality=90)
                    enc.stdin.write(im.tobytes())
            finally:
                dec.stdout.close();code=dec.wait()
                if code:raise RuntimeError('Decoder failed')
            cursor+=c['frames']
    finally:
        enc.stdin.close();code=enc.wait()
        if code:raise RuntimeError('Encoder failed')
    (out/f'scene_{i:03}.receipt.json').write_text(json.dumps({'request':render_receipt(data,root,i),'output_sha256':file_hash(dest)},ensure_ascii=False,indent=2))
    return dest

def stamp(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def finalize(data,root,out):
    srt=[];chapters=[];cursor=0
    for i,s in enumerate(data['scenes']):
        stored=json.loads((out/f'scene_{i:03}.receipt.json').read_text())
        if stored.get('request')!=render_receipt(data,root,i) or stored.get('output_sha256')!=file_hash(out/f'scene_{i:03}.mp4'):raise ValueError('Stale render: manifest, inputs, code or output changed')
        info=probe(out/f'scene_{i:03}.mp4');v=next(x for x in info['streams'] if x['codec_type']=='video')
        if int(v['nb_frames'])!=s['frames']:raise ValueError('Rendered frame count mismatch')
        if not chapters or chapters[-1][1]!=s['chapter']:chapters.append([cursor,s['chapter']])
        for c in s.get('captions',[]):
            lead=data.get('audio_lead',.25);srt.extend([str(len(srt)//4+1),f'{stamp(cursor+c["start"]+lead)} --> {stamp(cursor+c["end"]+lead)}',c['text'],''])
        cursor+=s['frames']/FPS
    (out/'film.srt').write_text('\n'.join(srt));(out/'chapters.json').write_text(json.dumps(chapters,ensure_ascii=False,indent=2))
    (out/'concat.txt').write_text(''.join(f"file 'scene_{i:03}.mp4'\n" for i in range(len(data['scenes']))))
    meta=[';FFMETADATA1']
    for j,(start,title) in enumerate(chapters):
        end=chapters[j+1][0] if j+1<len(chapters) else cursor
        safe=title.replace('\\','\\\\').replace('\n',' ').replace('=','\\=').replace(';','\\;').replace('#','\\#')
        meta+=['[CHAPTER]','TIMEBASE=1/1000',f'START={round(start*1000)}',f'END={round(end*1000)}',f'title={safe}']
    (out/'chapters.ffmeta').write_text('\n'.join(meta))
    # Decode scene audio to exact video durations and encode one continuous AAC track.
    # Copy-concatenating independently encoded AAC can accumulate encoder padding.
    with wave.open(str(out/'aligned-audio.wav'),'wb') as audio:
        audio.setnchannels(2);audio.setsampwidth(2);audio.setframerate(48000)
        for i,scene in enumerate(data['scenes']):
            duration=scene['frames']/FPS
            raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(out/f'scene_{i:03}.mp4'),'-vn','-af',f'apad,atrim=duration={duration}', '-ac','2','-ar','48000','-f','s16le','pipe:1'])
            expected=scene['frames']*2000*4
            if len(raw)!=expected:raise ValueError('Audio duration not frame-aligned')
            audio.writeframesraw(raw)
    subprocess.run(['ffmpeg','-v','error','-n','-f','concat','-safe','0','-i',str(out/'concat.txt'),'-i',str(out/'chapters.ffmeta'),'-i',str(out/'aligned-audio.wav'),'-map','0:v:0','-map','2:a:0','-map_metadata','1','-map_chapters','1','-c:v','copy','-c:a','aac','-b:a','128k','-t',str(cursor),'-movflags','+faststart',str(out/'film.mp4')],check=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('--out');p.add_argument('--validate',action='store_true');p.add_argument('--scene',type=int,action='append');p.add_argument('--finalize',action='store_true');a=p.parse_args()
    manifest=Path(a.manifest).resolve();root=manifest.parent;data=json.loads(manifest.read_text());validate(data,root)
    font=data['font'];g.FONT=str(resolve(root,font['path']));g.BOLD_INDEX=font.get('bold_index',0);g.REGULAR_INDEX=font.get('regular_index',0);g.ft(35)
    if a.validate:print('Manifest and media valid');raise SystemExit()
    if not a.out:p.error('--out is required for rendering')
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    if a.finalize:finalize(data,root,out)
    else:
        for i in (a.scene if a.scene is not None else range(len(data['scenes']))):render_scene(data,root,out,i);print('rendered',i,flush=True)
        if a.scene is None:finalize(data,root,out)
