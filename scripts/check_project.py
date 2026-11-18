"""Persist unit tests and Streamlit interaction checks in outputs/verification."""
import io
import json
import os
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0,str(ROOT))
os.environ['MPLBACKEND']='Agg'

output=ROOT/'outputs'/'verification'
output.mkdir(parents=True,exist_ok=True)
log=io.StringIO()
suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
tests=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
(output/'unit_tests.txt').write_text(log.getvalue(),encoding='utf-8')
print(log.getvalue(),flush=True)
report=dict(unit_tests_run=tests.testsRun,unit_failures=len(tests.failures),unit_errors=len(tests.errors))

from streamlit.testing.v1 import AppTest
app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=120).run()
assert not app.exception,[e.message for e in app.exception]
assert len(app.tabs)==4
assert len(app.metric)==4
report['streamlit_initial_metrics']={m.label:m.value for m in app.metric}
app.number_input[1].set_value(100.0).run()
assert not app.exception,[e.message for e in app.exception]
report['streamlit_reference_input']=True
app.checkbox[0].check().run()
assert not app.exception,[e.message for e in app.exception]
report['streamlit_manual_threshold']=True
# Invalid rules produce a user-facing error instead of an exception.
whole=next(s for s in app.slider if s.label=='Nguyên nếu tỷ lệ chiều dài từ')
whole.set_value(.60).run()
assert not app.exception
assert any('broken_max' in e.value for e in app.error)
report['streamlit_invalid_rules_message']=True

# Exercise the integrated demo through the same app used for real images.
whole.set_value(.80).run()
assert not app.exception,[e.message for e in app.exception]
app.selectbox[0].select(str(Path('dataset')/'synthetic_demo'/'scene.png')).run()
assert not app.exception,[e.message for e in app.exception]
assert app.metric[0].value=='5'
assert app.metric[2].value=='0'
report['streamlit_synthetic_demo_preset']=True
report['streamlit_synthetic_metrics']={m.label:m.value for m in app.metric}
report['visual_browser_check']='Unavailable: Windows Computer Use could not determine current browser URL; no live visual verification claimed.'
(output/'project_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
if not tests.wasSuccessful():
    raise SystemExit(1)
