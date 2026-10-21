"""Inspect an explicit local character profile without exposing provider credentials."""
import argparse,json
from pathlib import Path
from media_contract import file_hash
ASSETS=('reference_image','voice_sample','benchmark_video','renderer','production_notes','dependency_manifest')
def inspect(path,dependencies=False):
 path=Path(path).expanduser().resolve();data=json.loads(path.read_text());result={'name':data['name'],'assets':{}}
 for key in ASSETS:
  spec=data.get(key)
  if not spec:result['assets'][key]={'present':False,'status':'missing'};continue
  file=Path(spec['path']).expanduser()
  if not file.is_absolute():file=path.parent/file
  item={'present':file.is_file(),'status':'missing'}
  if item['present']:
   if spec.get('sha256'):
    item['hash_matches']=file_hash(file)==spec['sha256'];item['status']='verified' if item['hash_matches'] else 'changed'
   else:item['status']='unverified-hash'
  result['assets'][key]=item
  if key=='dependency_manifest' and dependencies and item['present']:
   manifest=json.loads(file.read_text());root=Path(manifest['root']).expanduser()
   if not root.is_absolute():root=file.parent/root
   result['dependencies']=[{'file':entry['path'],'verified':(root/entry['path']).is_file() and file_hash(root/entry['path'])==entry['sha256']} for entry in manifest['files']]
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['inspect']);p.add_argument('profile');p.add_argument('--require',action='append',choices=ASSETS);p.add_argument('--dependencies',action='store_true');a=p.parse_args();result=inspect(a.profile,a.dependencies)
 print(json.dumps(result,ensure_ascii=False,indent=2))
 if any(result['assets'][key]['status']!='verified' for key in (a.require or ['reference_image'])) or (a.dependencies and (not result.get('dependencies') or not all(x['verified'] for x in result['dependencies']))):raise SystemExit(1)
