"""Verify scene/final timing, audio delay against the source and full-file decode."""
import argparse,json,subprocess
from pathlib import Path
import numpy as np
from scipy.signal import correlate,correlation_lags
from media_contract import probe,resolve,validate,render_receipt,file_hash

def samples(path):
 raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-vn','-ac','2','-ar','8000','-f','f32le','pipe:1'])
 return np.frombuffer(raw,dtype=np.float32).reshape(-1,2)

def delay(target,source):
 # Compare each rendered channel to its own original, preserving legitimate stereo differences.
 norm=float(np.linalg.norm(target)*np.linalg.norm(source))
 if norm<1e-5:return {'status':'unverified-silent'}
 c=correlate(target,source,method='fft')/norm;lags=correlation_lags(len(target),len(source));mask=(lags>=-4000)&(lags<=8000)
 best=int(np.argmax(c[mask]));lag=int(lags[mask][best]);peak=float(c[mask][best])
 # Periodic signals can have equally plausible peaks far apart; never call that proven alignment.
 alternatives=mask & (abs(lags-lag)>80)
 second=float(np.max(c[alternatives])) if np.any(alternatives) else 0
 status='passed' if peak>=.65 and peak-second>=.01 else 'unverified-ambiguous'
 return {'status':status,'delay_ms':lag/8,'correlation':round(peak,4),'peak_margin':round(peak-second,4)}

def run(manifest,out):
 f=Path(manifest).resolve();data=json.loads(f.read_text());validate(data,f.parent);out=Path(out)
 report={'scenes':[],'speed':1.0,'decode':'pending','audio_status':'passed'}
 for i,s in enumerate(data['scenes']):
  stored=json.loads((out/f'scene_{i:03}.receipt.json').read_text())
  if stored.get('request')!=render_receipt(data,f.parent,i) or stored.get('output_sha256')!=file_hash(out/f'scene_{i:03}.mp4'):raise ValueError('Stale rendered scene')
  path=out/f'scene_{i:03}.mp4';meta=probe(path);v=next(v for v in meta['streams'] if v['codec_type']=='video')
  if int(v['nb_frames'])!=s['frames']:raise ValueError('Frame mismatch')
  sig=samples(path);src=samples(resolve(f.parent,s['audio']));channels=[delay(sig[:,j],src[:,j]) for j in range(2)]
  expected=data.get('audio_lead',.25)*1000
  for check in channels:
   if check['status']=='passed' and abs(check['delay_ms']-expected)>2:raise ValueError(f'Scene {i}: wrong audio delay')
  if any(c['status']!='passed' for c in channels):report['audio_status']='needs_listening_or_better_signal'
  report['scenes'].append({'scene':i,'frames':s['frames'],'channels':channels})
 final=out/'film.mp4';meta=probe(final);v=next(v for v in meta['streams'] if v['codec_type']=='video');total=sum(s['frames'] for s in data['scenes'])
 if (v['width'],v['height'],v['r_frame_rate'])!=(1920,1080,'24/1'):raise ValueError('Wrong final dimensions/fps')
 if not any(x['codec_type']=='audio' for x in meta['streams']):raise ValueError('Missing final audio')
 if int(v['nb_frames'])!=total:raise ValueError('Final frame count differs from manifest')
 if abs(float(v['duration'])-total/24)>1/24+.001:raise ValueError('Final video duration differs from manifest')
 # Verify concat is exactly the scene video stream sequence, not merely a decodable file of equal length.
 def hashes(path):
  raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:v:0','-f','framemd5','-'])
  return [line.rsplit(b',',1)[-1].strip() for line in raw.splitlines() if line and not line.startswith(b'#')]
 expected_hashes=[]
 for i in range(len(data['scenes'])):expected_hashes.extend(hashes(out/f'scene_{i:03}.mp4'))
 if hashes(final)!=expected_hashes:raise ValueError('Final video differs from rendered scene order')
 chapter_data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_chapters','-of','json',str(final)],text=True))['chapters']
 expected_chapters=[];cursor=0
 for scene in data['scenes']:
  if not expected_chapters or expected_chapters[-1][1]!=scene['chapter']:expected_chapters.append([cursor,scene['chapter']])
  cursor+=scene['frames']/24
 if len(chapter_data)!=len(expected_chapters):raise ValueError('Wrong chapter count')
 for j,(chapter,(start,title)) in enumerate(zip(chapter_data,expected_chapters)):
  end=expected_chapters[j+1][0] if j+1<len(expected_chapters) else cursor
  if abs(float(chapter['start_time'])-start)>.002 or abs(float(chapter['end_time'])-end)>.002 or chapter.get('tags',{}).get('title')!=title:raise ValueError('Wrong chapter metadata')
 joined=np.concatenate([samples(out/f'scene_{i:03}.mp4')[:s['frames']*8000//24] for i,s in enumerate(data['scenes'])])
 final_audio=samples(final)
 audio_checks=[delay(final_audio[:,j],joined[:,j]) for j in range(2)]
 for check in audio_checks:
  if check['status']=='passed' and abs(check['delay_ms'])>2:raise ValueError('Final audio differs from scene assembly')
 if any(c['status']!='passed' for c in audio_checks):report['audio_status']='needs_listening_or_better_signal'
 report['final_audio']=audio_checks
 subprocess.run(['ffmpeg','-v','error','-i',str(final),'-f','null','-'],check=True)
 report.update(decode='passed',frames=total,duration=float(meta['format']['duration']))
 (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));return report

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');p.add_argument('output');a=p.parse_args();result=run(a.manifest,a.output);print(json.dumps(result,ensure_ascii=False))
 if result['audio_status']!='passed':raise SystemExit(2)
