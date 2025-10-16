#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Translate chinese fields in nba.json to English.

Behavior:
- Reads nba.json from project root
- Backs up to nba_zh_backup.json (once per run if not exists)
- Translates per-item fields: title, detail (zh -> en)
- Preserves list length and object key order
- Writes back to nba.json with 2-space indentation

Backends (same as HTML translation script):
- DeepL: set DEEPL_API_KEY
- Azure Translator: set AZURE_TRANSLATOR_KEY and AZURE_TRANSLATOR_ENDPOINT

If no backend keys are present, the script will print guidance and exit without modifying the file.
"""

import os
import json
import uuid
import io
from collections import OrderedDict
try:
    # Py3
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
except Exception:
    # Py2
    from urllib2 import Request, urlopen, HTTPError  # type: ignore


ROOT = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(ROOT, 'nba.json')
BACKUP_PATH = os.path.join(ROOT, 'nba_zh_backup.json')


def has_chinese(s):
    if not s:
        return False
    try:
        import re
        return re.search(u"[\u4e00-\u9fff]", s) is not None
    except Exception:
        return False


def translate_texts(texts):
    if not texts:
        return []
    deepl_key = os.environ.get('DEEPL_API_KEY')
    az_key = os.environ.get('AZURE_TRANSLATOR_KEY')
    az_ep = os.environ.get('AZURE_TRANSLATOR_ENDPOINT')
    if deepl_key:
        return translate_deepl(texts, deepl_key)
    if az_key and az_ep:
        return translate_azure(texts, az_key, az_ep)
    return None  # signal no backend


def translate_deepl(texts, api_key):
    url = 'https://api-free.deepl.com/v2/translate'
    params = [('auth_key', api_key), ('target_lang', 'EN')]
    for t in texts:
        params.append(('text', t))
    body = '&'.join(['{}={}'.format(k, _percent_encode(v)) for k, v in params])
    req = Request(url, data=body.encode('utf-8'), headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        resp = urlopen(req)
        data = json.loads(resp.read().decode('utf-8', 'ignore'))
        trans = [item['text'] for item in data.get('translations', [])]
        if len(trans) != len(texts):
            trans = trans + texts[len(trans):]
        return trans
    except Exception as e:
        print('DeepL error:', e)
        return texts


def translate_azure(texts, api_key, endpoint):
    url = endpoint.rstrip('/') + '/translate?api-version=3.0&to=en'
    body = json.dumps([{ 'text': t } for t in texts]).encode('utf-8')
    headers = {
        'Ocp-Apim-Subscription-Key': api_key,
        'Content-Type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }
    req = Request(url, data=body, headers=headers)
    try:
        resp = urlopen(req)
        data = json.loads(resp.read().decode('utf-8', 'ignore'))
        out = []
        for item in data:
            ts = item.get('translations') or []
            out.append(ts[0].get('text', '') if ts else '')
        if len(out) != len(texts):
            out = out + texts[len(out):]
        return out
    except Exception as e:
        print('Azure error:', e)
        return texts


def _percent_encode(value):
    try:
        from urllib.parse import quote_plus  # py3
    except Exception:
        from urllib import quote_plus  # py2
    if isinstance(value, bytes):
        value = value.decode('utf-8', 'ignore')
    return quote_plus(value)


def backup_once():
    if not os.path.exists(JSON_PATH):
        print('nba.json not found')
        return False
    if os.path.exists(BACKUP_PATH):
        return True
    with io.open(JSON_PATH, 'rb') as f:
        data = f.read()
    with io.open(BACKUP_PATH, 'wb') as f:
        f.write(data)
    print('Backup created at', BACKUP_PATH)
    return True


def main():
    if not os.path.exists(JSON_PATH):
        print('nba.json not found in project root')
        return

    # Detect backend availability
    has_backend = bool(os.environ.get('DEEPL_API_KEY') or (
        os.environ.get('AZURE_TRANSLATOR_KEY') and os.environ.get('AZURE_TRANSLATOR_ENDPOINT')
    ))
    if not has_backend:
        print('No translation backend configured. Set DEEPL_API_KEY or AZURE_TRANSLATOR_KEY + AZURE_TRANSLATOR_ENDPOINT')
        return

    backup_once()

    with io.open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.loads(f.read(), object_pairs_hook=OrderedDict)

    if not isinstance(data, list):
        print('Unexpected JSON format; expected a list of items')
        return

    # Gather all chunks to translate in sequence to leverage batching
    texts = []
    positions = []  # (item_index, field_name)

    for i, item in enumerate(data):
        # only process title/detail if Chinese present
        for field in ('title', 'detail'):
            val = item.get(field)
            if isinstance(val, (str, unicode)) if 'unicode' in dir(__builtins__) else isinstance(val, str):  # py2/py3
                if has_chinese(val):
                    texts.append(val)
                    positions.append((i, field))

    if not texts:
        print('No Chinese content found in nba.json')
        return

    translated = translate_texts(texts)
    if translated is None:
        print('No translation performed (backend missing).')
        return

    # Apply translations
    for (idx, field), new_val in zip(positions, translated):
        data[idx][field] = new_val

    # Write back with 2-space indentation, stable separators
    with io.open(JSON_PATH, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2, separators=(',', ': ')))

    print('Translated {} fields across {} items.'.format(len(texts), len(data)))


if __name__ == '__main__':
    main()


