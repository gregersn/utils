import json
import os
from os.path import expanduser

def load_settings(filename: str = None):
    if filename is None:
        filename = os.path.join(expanduser("~"), '.gsnutils.json')

    with open(filename, 'r') as f:
        return json.load(f)

    return {}

SETTINGS = load_settings()
