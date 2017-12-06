import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../include/AK/WwiseAuthoringAPI/py'))
from waapi import WAAPI_URI
import requests
import json
import codecs


sys.stdout = codecs.getwriter('utf8')(sys.stdout, 'strict')

payload = {
    'uri': WAAPI_URI.ak_wwise_core_getinfo,
    'options': {},
    'args': {}    
}

r = requests.post("http://localhost:8090/waapi", data=json.dumps(payload))
print(r.status_code, r.reason)

print(r.text)