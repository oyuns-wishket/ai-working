import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
S=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(S))
import media_contract as c
import profile as profiles
class ContractTests(unittest.TestCase):
 def setUp(self):
  self.data={'scenes':[{'frames':144,'audio':'voice.mp3','cuts':[{'video':'clip.mp4','frames':144,'source_in':2,'speed':1,'reviewed':True}],'captions':[{'start':0,'end':4,'text':'자료 확인'}]}]}
 def test_valid_timing(self):c.validate(self.data,Path('.'),media=False)
 def test_no_stretch(self):
  self.data['scenes'][0]['cuts'][0]['speed']=.5
  with self.assertRaisesRegex(ValueError,'stretching'):c.validate(self.data,Path('.'),False)
 def test_gap_rejected(self):
  self.data['scenes'][0]['cuts'][0]['frames']=120
  with self.assertRaisesRegex(ValueError,'coverage'):c.validate(self.data,Path('.'),False)
 def test_unreviewed_rejected(self):
  self.data['scenes'][0]['cuts'][0]['reviewed']=False
  with self.assertRaisesRegex(ValueError,'Inspect'):c.validate(self.data,Path('.'),False)
 def test_source_overrun_rejected(self):
  with patch.object(c,'probe',return_value={'streams':[{'codec_type':'video','duration':'7'}],'format':{'duration':'7'}}):
   with self.assertRaisesRegex(ValueError,'beyond'):c.validate(self.data,Path('.'))
 def test_narration_truncation_rejected(self):
  with patch.object(c,'probe',side_effect=[{'streams':[{'codec_type':'video','duration':'10'}],'format':{'duration':'10'}},{'format':{'duration':'6'}}]):
   with self.assertRaisesRegex(ValueError,'truncated'):c.validate(self.data,Path('.'))
 def test_caption_delay_once(self):
  self.data['scenes'][0]['captions'][0]['end']=6
  with self.assertRaisesRegex(ValueError,'Caption'):c.validate(self.data,Path('.'),False)
 def test_profile_drift_is_detected(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);(r/'cat.png').write_bytes(b'reference')
   (r/'profile.json').write_text(json.dumps({'name':'kitten','reference_image':{'path':'cat.png','sha256':'wrong'}}))
   result=profiles.inspect(r/'profile.json');self.assertTrue(result['assets']['reference_image']['present']);self.assertFalse(result['assets']['reference_image']['hash_matches'])
if __name__=='__main__':unittest.main()
