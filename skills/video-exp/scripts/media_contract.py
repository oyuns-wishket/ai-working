"""Validate cut coverage, source intervals and caption/audio timing without rendering."""
import json, math, subprocess
from pathlib import Path
FPS=24

def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],text=True))

def resolve(root, value):
    p=Path(value).expanduser()
    return p if p.is_absolute() else root/p

def validate(data, root, media=True):
    if data.get('fps',24)!=FPS: raise ValueError('Baseline renderer uses 24fps')
    if not data.get('scenes'): raise ValueError('No scenes')
    lead=data.get('audio_lead',.25)
    if not isinstance(lead,(int,float)) or not math.isfinite(lead) or lead<0:raise ValueError('Invalid audio_lead')
    for i,s in enumerate(data['scenes']):
        if not isinstance(s['frames'],int) or s['frames']<=0:raise ValueError('Positive integer frames required')
        if sum(c['frames'] for c in s['cuts'])!=s['frames']:raise ValueError(f'Scene {i}: cut coverage')
        for c in s['cuts']:
            if c.get('speed',1)!=1:raise ValueError('Time stretching is forbidden')
            if c.get('reviewed') is not True:raise ValueError('Inspect physical action before rendering')
            if not isinstance(c['frames'],int) or c['frames']<=0 or not math.isfinite(c.get('source_in',0)) or c.get('source_in',0)<0:raise ValueError('Invalid source interval')
            if media:
                p=probe(resolve(root,c['video']))
                v=next(x for x in p['streams'] if x['codec_type']=='video')
                duration=float(v.get('duration',p['format']['duration']))
                if c.get('source_in',0)+c['frames']/FPS>duration+.001:raise ValueError('Cut extends beyond source')
        for caption in s.get('captions',[]):
            if not 0<=caption['start']<caption['end']<=s['frames']/FPS-lead+.05:raise ValueError('Caption outside narration interval')
        if media:
            audio=probe(resolve(root,s['audio']))
            if float(audio['format']['duration'])+lead>s['frames']/FPS+.05:raise ValueError('Narration would be truncated')
        for event in s.get('panels',[])+s.get('props',[]):
            if not 0<=event['start']<event['end']<=s['frames']/FPS+.001:raise ValueError('Overlay event outside scene')



def file_hash(path):
    import hashlib
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()

def render_receipt(data,root,i):
    scene=data['scenes'][i]
    inputs=[scene['audio'],data['font']['path']]+[c['video'] for c in scene['cuts']]
    return {'scene':scene,'settings':{k:data.get(k) for k in ['title','panel_heading','fps','audio_lead','font']},
            'inputs':{str(value):file_hash(resolve(root,value)) for value in sorted(set(inputs))},
            'code':{name:file_hash(Path(__file__).with_name(name)) for name in ['render.py','graphics.py','media_contract.py']}}
