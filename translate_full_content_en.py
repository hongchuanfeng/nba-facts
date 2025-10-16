#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Translate all Chinese text content in root-level HTML files to English.

Features:
- Updates <html lang> to en
- Translates visible text in a safe set of tags: title, h1-h6, p, li, span, a, blockquote, button, small, strong, em, label, figcaption
- Translates common attributes: alt, title, aria-label, placeholder, content (for meta description)
- Preserves HTML structure and spacing

Translation backends (auto-detected by environment variables):
- DeepL: set DEEPL_API_KEY
- Azure Translator: set AZURE_TRANSLATOR_KEY and AZURE_TRANSLATOR_ENDPOINT (v3.0)

If no backend keys are present, the script will skip translation and print guidance.
"""
from __future__ import print_function
import os
import re
import json
import uuid
import glob
try:
    # Python 3
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
except Exception:
    # Python 2
    from urllib2 import Request, urlopen, HTTPError  # type: ignore


ROOT = os.path.dirname(os.path.abspath(__file__))


TAG_TEXT_PATTERN = re.compile(
    r"(<(?P<tag>title|h[1-6]|p|li|span|a|blockquote|button|small|strong|em|label|figcaption)(?P<attrs>[^>]*)>)(?P<text>[^<]+)(</\2>)",
    re.IGNORECASE
)

ATTRS_TO_TRANSLATE = [
    'alt', 'title', 'aria-label', 'placeholder'
]


def has_chinese(s):
    if not s:
        return False
    return re.search(u"[\u4e00-\u9fff]", s) is not None


def translate_texts(texts):
    """Translate a list of strings zh->en using available backend. Returns list of translated strings (same length)."""
    if not texts:
        return []

    deepl_key = os.environ.get('DEEPL_API_KEY')
    az_key = os.environ.get('AZURE_TRANSLATOR_KEY')
    az_ep = os.environ.get('AZURE_TRANSLATOR_ENDPOINT')

    if deepl_key:
        return translate_deepl(texts, deepl_key)
    if az_key and az_ep:
        return translate_azure(texts, az_key, az_ep)

    # No backend available, return original
    return texts


def translate_deepl(texts, api_key):
    url = 'https://api-free.deepl.com/v2/translate'
    # Build form data
    params = [('auth_key', api_key), ('target_lang', 'EN')]
    for t in texts:
        params.append(('text', t))
    body = '&'.join(['{}={}'.format(k, _percent_encode(v)) for k, v in params])
    req = Request(url, data=body.encode('utf-8'), headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        resp = urlopen(req)
        data = json.loads(resp.read().decode('utf-8', 'ignore'))
        trans = [item['text'] for item in data.get('translations', [])]
        # pad if mismatch
        if len(trans) != len(texts):
            trans = trans + texts[len(trans):]
        return trans
    except HTTPError as e:
        print('DeepL error:', e)
        return texts
    except Exception as e:
        print('DeepL error:', e)
        return texts


def translate_azure(texts, api_key, endpoint):
    # Azure Translator v3.0
    url = endpoint.rstrip('/') + '/translate?api-version=3.0&to=en'
    payload = [{"text": t} for t in texts]
    body = json.dumps(payload).encode('utf-8')
    headers = {
        'Ocp-Apim-Subscription-Key': api_key,
        'Content-Type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }
    req = Request(url, data=body, headers=headers)
    try:
        resp = urlopen(req)
        data = json.loads(resp.read().decode('utf-8', 'ignore'))
        result = []
        for item in data:
            translations = item.get('translations') or []
            if translations:
                result.append(translations[0].get('text', ''))
            else:
                result.append('')
        if len(result) != len(texts):
            result = result + texts[len(result):]
        return result
    except HTTPError as e:
        print('Azure error:', e)
        return texts
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


def update_lang_attr(html):
    return re.sub(r'(<html\s+[^>]*?lang=\")zh(?:-CN)?(\")', r'\1en\2', html, flags=re.IGNORECASE)


def translate_attributes(html):
    # Translate specific attributes when they contain Chinese
    def repl(m):
        before = m.group(0)
        attr = m.group('attr')
        val = m.group('val')
        if has_chinese(val):
            new_val = translate_texts([val])[0]
            return before.replace(val, new_val)
        return before

    # Build a regex for each attribute
    for attr in ATTRS_TO_TRANSLATE:
        pattern = re.compile(r'\s' + attr + r'=\"(?P<val>[^\"]+)\"', re.IGNORECASE)
        html = pattern.sub(lambda m: ' {}="{}"'.format(attr, translate_texts([m.group('val')])[0]) if has_chinese(m.group('val')) else m.group(0), html)
    return html


def translate_visible_text(html):
    # Find simple text nodes inside selected tags (no nested tags). For nested content, this will be applied iteratively but remains conservative.
    chunks = []
    positions = []
    for m in TAG_TEXT_PATTERN.finditer(html):
        text = m.group('text')
        if has_chinese(text.strip()):
            chunks.append(text)
            positions.append((m.start('text'), m.end('text')))

    if not chunks:
        return html

    translated = translate_texts(chunks)
    # Rebuild string with replacements
    html_list = list(html)
    for (start, end), new_text in zip(positions, translated):
        # replace in place preserving length changes by slicing
        html_list[start:end] = list(new_text)
    return ''.join(html_list)


def process_file(path):
    try:
        with open(path, 'rb') as f:
            data = f.read()
        try:
            html = data.decode('utf-8')
        except Exception:
            html = data.decode('utf-8', 'ignore')
    except Exception:
        return False

    original = html
    html = update_lang_attr(html)
    html = translate_attributes(html)
    html = translate_visible_text(html)
    # Also translate <meta name="description" content="...">
    meta_pat = re.compile(r'(<meta\s+name=\"description\"\s+content=\")(.*?)\"', re.IGNORECASE)
    def meta_repl(m):
        val = m.group(2)
        if has_chinese(val):
            t = translate_texts([val])[0]
            return m.group(1) + t + '"'
        return m.group(0)
    html = meta_pat.sub(meta_repl, html)

    changed = (html != original)
    if changed:
        with open(path, 'wb') as f:
            f.write(html.encode('utf-8'))
    return changed


def main():
    html_files = glob.glob(os.path.join(ROOT, '*.html'))
    if not html_files:
        print('No root-level HTML files found.')
        return

    # Detect backend
    backend = 'none'
    if os.environ.get('DEEPL_API_KEY'):
        backend = 'deepl'
    elif os.environ.get('AZURE_TRANSLATOR_KEY') and os.environ.get('AZURE_TRANSLATOR_ENDPOINT'):
        backend = 'azure'

    if backend == 'none':
        print('No translation backend configured. Set DEEPL_API_KEY or AZURE_TRANSLATOR_KEY + AZURE_TRANSLATOR_ENDPOINT to enable translation.')

    total = 0
    for p in html_files:
        if os.path.basename(p).lower().startswith('privacy'):
            # still process; requirement is all root-level html
            pass
        if process_file(p):
            total += 1

    print('Processed {} files{}.'.format(total, '' if backend != 'none' else ' (no-op without API key)'))


if __name__ == '__main__':
    main()


