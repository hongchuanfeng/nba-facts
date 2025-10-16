# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import os
import re
try:
    from urllib.parse import quote
except Exception:
    # Python 2 fallback
    from urllib import quote

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def read_text(path):
    if hasattr(__builtins__, 'open'):
        try:
            # Python 3
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except TypeError:
            pass
    import io
    with io.open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_text(path, content):
    if hasattr(__builtins__, 'open'):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
                return
        except TypeError:
            pass
    import io
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def find_div_block(html, class_selector):
    """
    Find the div with exact class attribute value equal to class_selector and return:
    - start index of opening <div ...>
    - end index (exclusive) of opening tag '>'
    - start index of closing </div>
    - end index (exclusive) of closing tag
    The function attempts to balance nested <div> ... </div> blocks starting at the matched div.
    """
    # Match the opening div with exact class attribute
    # Allow additional attributes order-insensitive by matching class first, then anything until '>'
    pattern = re.compile(r'<div\s+[^>]*class\s*=\s*"' + re.escape(class_selector) + r'"[^>]*>', re.IGNORECASE)
    m = pattern.search(html)
    if not m:
        return -1, -1, -1, -1
    open_start = m.start()
    open_end = m.end()

    # Now from open_end, walk to find the matching closing </div> by counting nested divs
    idx = open_end
    depth = 1
    # Precompile simple tags
    open_tag = re.compile(r'<div\b', re.IGNORECASE)
    close_tag = re.compile(r'</div\s*>', re.IGNORECASE)
    while depth > 0:
        next_open = open_tag.search(html, idx)
        next_close = close_tag.search(html, idx)
        if not next_close:
            # Unbalanced
            return open_start, open_end, -1, -1
        if next_open and next_open.start() < next_close.start():
            depth += 1
            idx = next_open.end()
        else:
            depth -= 1
            idx = next_close.end()
            if depth == 0:
                close_start = next_close.start()
                close_end = next_close.end()
                return open_start, open_end, close_start, close_end
    return open_start, open_end, -1, -1


def extract_probable_player_name(title):
    """
    Heuristic: if the title starts with 2-4 consecutive CJK characters likely forming a name,
    or contains well-known separators, extract that block as a name.
    """
    # Try to capture first 2-4 consecutive CJK characters at start
    m = re.match(r'^[\u4e00-\u9fa5]{2,4}', title)
    if m:
        return m.group(0)
    # Try patterns like 姓名·姓名 or 含有单引号的人名片段
    m2 = re.search(r'([\u4e00-\u9fa5]{2,4})[··\.\'\"“”\' ]?', title)
    if m2:
        return m2.group(1)
    # Latin names fallback: grab first word
    m3 = re.match(r'([A-Za-z]+\s+[A-Za-z]+)', title)
    if m3:
        return m3.group(1)
    return None


def build_enhanced_inner(title, detail_text):
    # split paragraphs by full stop U+3002 while keeping content
    parts = [p.strip() for p in re.split(u'\u3002', detail_text) if p.strip()]
    parts = [p + u'。' for p in parts]
    if not parts:
        parts = [detail_text]
    # build paragraphs html
    para_html = ''
    for i, p in enumerate(parts):
        esc = p.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        if i == 0:
            para_html += (
                '                    <p class="text-lg leading-relaxed whitespace-pre-line first-letter:text-5xl first-letter:font-bold first-letter:text-nba-purple first-letter:mr-2 first-letter:float-left">'
                + esc + '</p>\n'
            )
        else:
            para_html += '                    <p class="text-lg leading-relaxed whitespace-pre-line">' + esc + '</p>\n'
    # quote snippet
    first_sentence = parts[0].strip() if parts else ''
    if len(first_sentence) > 60:
        first_sentence = first_sentence[:60] + '...'
    first_sentence = first_sentence.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # name badge
    name = extract_probable_player_name(title) or '冷知识'
    header = (
        '                <!-- 信息徽章与阅读提示 -->\n'
        '                <div class="flex flex-wrap items-center gap-2 mb-6 text-sm">\n'
        '                    <span class="px-3 py-1 rounded-full bg-nba-purple/10 text-nba-purple">' + name + '</span>\n'
        '                    <span class="px-3 py-1 rounded-full bg-nba-gold/10 text-nba-gold">冷知识</span>\n'
        '                    <span class="ml-auto text-gray-500 flex items-center"><i class="fa fa-clock-o mr-1"></i> 3 min read</span>\n'
        '                </div>\n\n'
        '                <!-- 渐变分隔线 -->\n'
        '                <div class="relative mb-6">\n'
        '                    <div class="h-1 w-24 bg-gradient-to-r from-nba-purple to-nba-gold rounded"></div>\n'
        '                </div>\n\n'
        '                <!-- 正文（首字下沉、美化排版） -->\n'
        '                <div class="prose lg:prose-xl max-w-none text-gray-800">\n'
    )
    footer = (
        '                </div>\n\n'
        '                <!-- 侧栏引述与提示 -->\n'
        '                <div class="mt-8 grid md:grid-cols-5 gap-6 items-start">\n'
        '                    <div class="md:col-span-3">\n'
        '                        <div class="bg-nba-light/60 border border-gray-100 rounded-lg p-4">\n'
        '                            <div class="flex items-center text-nba-purple font-medium mb-2"><i class="fa fa-lightbulb-o mr-2"></i>小贴士</div>\n'
        '                            <p class="text-gray-700 leading-relaxed">持续的基本功与专注力，决定了稳定的比赛表现。</p>\n'
        '                        </div>\n'
        '                    </div>\n'
        '                    <div class="md:col-span-2">\n'
        '                        <blockquote class="rounded-lg bg-gradient-to-br from-nba-purple/10 to-nba-gold/10 border-l-4 border-nba-purple p-4 italic text-gray-700">\n'
        '                            "' + first_sentence + '"\n'
        '                        </blockquote>\n'
        '                    </div>\n'
        '                </div>\n'
    )
    return header + para_html + footer


def build_detail_block(detail_text):
    # Preserve line breaks
    escaped = detail_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return (
        '\n                <div class="prose lg:prose-xl max-w-none">\n'
        '                    <p class="text-lg leading-relaxed whitespace-pre-line">' + escaped + '</p>\n'
        '                </div>\n'
    )


def update_content_div(html, detail_text, title, local_link):
    open_start, open_end, close_start, close_end = find_div_block(html, 'p-6 md:p-8')
    if open_start == -1 or close_start == -1:
        return html  # no change if not found
    # nba_1.html 已单独优化，其他统一使用增强版
    if local_link != 'nba_1.html':
        inner = build_enhanced_inner(title, detail_text)
    else:
        inner = build_detail_block(detail_text)
    return html[:open_end] + inner + html[close_start:]


def update_hero_image(html, title):
    name = extract_probable_player_name(title)
    if not name:
        return html
    # Replace src of the first <img ... class="w-full h-full object-cover">
    # Build avatar URL (use ui-avatars with encoded name)
    try:
        # Python 3 path
        encoded = quote(name)
    except Exception:
        # Python 2 path: ensure bytes
        try:
            encoded = quote(name.encode('utf-8'))
        except Exception:
            encoded = quote(name)
    avatar_url = "https://ui-avatars.com/api/?name={}&background=552583&color=ffffff&size=512".format(encoded)
    img_pattern = re.compile(r'(<img\s+[^>]*class\s*=\s*"[^"<>]*\bw-full\s+h-full\s+object-cover\b[^"<>]*"[^>]*src\s*=\s*")([^"<>]+)("[^>]*>)', re.IGNORECASE)
    m = img_pattern.search(html)
    if not m:
        # Try without requiring src before class (replace any matching class img's src)
        img_class_pattern = re.compile(r'(<img\s+[^>]*class\s*=\s*"[^"<>]*\bw-full\s+h-full\s+object-cover\b[^"<>]*"[^>]*)(>)', re.IGNORECASE)
        m2 = img_class_pattern.search(html)
        if not m2:
            return html
        # Inject src attribute
        start, end = m2.start(1), m2.end(1)
        return html[:end] + ' src="{}"'.format(avatar_url) + html[end:]
    start, old_src, tail = m.group(1), m.group(2), m.group(3)
    return html[:m.start(1)] + start + avatar_url + tail + html[m.end(3):]


def find_grid_block(html):
    # Match div whose class contains the grid tokens regardless of order
    pattern = re.compile(
        r'<div\s+[^>]*class\s*=\s*"(?=[^"]*\bgrid\b)(?=[^"]*\bgrid-cols-1\b)(?=[^"]*\bmd:grid-cols-2\b)(?=[^"]*\blg:grid-cols-3\b)(?=[^"]*\bgap-6\b)[^"]*"[^>]*>',
        re.IGNORECASE,
    )
    m = pattern.search(html)
    if not m:
        return -1, -1, -1, -1
    open_start = m.start()
    open_end = m.end()
    # balance nested divs
    idx = open_end
    depth = 1
    open_tag = re.compile(r'<div\b', re.IGNORECASE)
    close_tag = re.compile(r'</div\s*>', re.IGNORECASE)
    while depth > 0:
        next_open = open_tag.search(html, idx)
        next_close = close_tag.search(html, idx)
        if not next_close:
            return open_start, open_end, -1, -1
        if next_open and next_open.start() < next_close.start():
            depth += 1
            idx = next_open.end()
        else:
            depth -= 1
            idx = next_close.end()
            if depth == 0:
                return open_start, open_end, next_close.start(), next_close.end()
    return open_start, open_end, -1, -1


def build_card_html(item, seed):
    title = item.get('title', '')
    detail = item.get('detail', '') or ''
    local_link = item.get('localLink', '#')
    # First 19 characters (unicode-safe), then ellipsis
    summary = detail[:19] + '...'
    # image: random placeholder by seed
    img_src = 'https://picsum.photos/id/{}/600/300'.format(seed)
    esc_title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    esc_summary = summary.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return (
        '                <a href="{href}" class="block">\n'
        '                    <div class="bg-white rounded-lg shadow-md overflow-hidden card-hover">\n'
        '                        <img src="{img}" alt="{alt}" class="w-full h-48 object-cover">\n'
        '                        <div class="p-4">\n'
        '                            <h4 class="font-bold text-lg mb-2">{title}</h4>\n'
        '                            <p class="text-gray-600 text-sm">{summary}</p>\n'
        '                        </div>\n'
        '                    </div>\n'
        '                </a>\n'
    ).format(href=local_link, img=img_src, alt=esc_title, title=esc_title, summary=esc_summary)


def update_related_grid(html, current_item, id_to_item):
    gid = current_item.get('id')
    if not isinstance(gid, int):
        return html
    # pick next three ids, wrap around if needed
    related_ids = [gid + 1, gid + 2, gid + 3]
    # wrap around to existing ids range
    max_id = max(id_to_item.keys()) if id_to_item else gid
    norm_ids = []
    for rid in related_ids:
        nid = rid
        if nid > max_id:
            nid = ((nid - 1) % max_id) + 1
        norm_ids.append(nid)
    related_items = [id_to_item[i] for i in norm_ids if i in id_to_item]
    if len(related_items) < 1:
        return html
    open_start, open_end, close_start, close_end = find_grid_block(html)
    if open_start == -1 or close_start == -1:
        return html
    cards = ''
    for idx, it in enumerate(related_items):
        seed = (it.get('id') or (idx + 1)) % 1000
        cards += build_card_html(it, seed)
    # Keep indentation similar
    inner = '\n' + cards + '            '
    return html[:open_end] + inner + html[close_start:]


def update_nav_links(html):
    nav_container = re.search(r'(\<div class=\"hidden md:flex[^\"]*[^>]*\>)([\s\S]*?)(\</div\>)', html)
    if not nav_container:
        # Try fallback: right-side container with only Home link
        right_div = re.search(r'(\<div\>)([\s\S]*?)(\</div\>)', html)
        if right_div and ('href="index.html"' in right_div.group(2)) and ('about.html' not in right_div.group(2)):
            addition = (
                '\n                <a href="about.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">\n'
                '                    <i class="fa fa-info-circle mr-1"></i> 关于我们\n'
                '                </a>\n'
                '                <a href="privacy.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">\n'
                '                    <i class="fa fa-shield mr-1"></i> 隐私政策\n'
                '                </a>'
            )
            new_inner = right_div.group(2) + addition
            return html[:right_div.start()] + right_div.group(1) + new_inner + right_div.group(3) + html[right_div.end():]
        return html
    head, inner, tail = nav_container.group(1), nav_container.group(2), nav_container.group(3)
    if 'about.html' in inner and 'privacy.html' in inner:
        return html
    addition = (
        '\n                <a href="about.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">\n'
        '                    <i class="fa fa-info-circle mr-1"></i> 关于我们\n'
        '                </a>\n'
        '                <a href="privacy.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">\n'
        '                    <i class="fa fa-shield mr-1"></i> 隐私政策\n'
        '                </a>'
    )
    new_inner = inner + addition
    return html[:nav_container.start()] + head + new_inner + tail + html[nav_container.end():]


def extract_index_footer():
    try:
        index_path = os.path.join(ROOT_DIR, 'index.html')
        src = read_text(index_path)
        m = re.search(r'(\<footer[\s\S]*?class=\"bg-nba-dark[\s\S]*?\</footer\>)', src)
        if m:
            return m.group(1)
    except Exception:
        return None
    return None


def replace_footer(html, footer_html):
    m = re.search(r'(\<footer[\s\S]*?class=\"bg-nba-dark[\s\S]*?\</footer\>)', html)
    if not m:
        return html
    return html[:m.start()] + footer_html + html[m.end():]


def replace_nav_block(html):
    # Find opening <nav ...>
    nav_open = re.search(r'<nav[^>]*>', html)
    nav_close = re.search(r'</nav>', html)
    if not nav_open or not nav_close or nav_close.start() < nav_open.end():
        return html
    opening = nav_open.group(0)
    # Standard navbar content (mobile-friendly)
    content = (
        '\n        <div class="container mx-auto px-4 py-3 flex justify-between items-center">\n'
        '            <div class="flex items-center space-x-2">\n'
        '                <i class="fa fa-basketball-ball text-2xl text-nba-gold"></i>\n'
        '                <h1 class="text-xl font-bold">NBA冷门知识库</h1>\n'
        '            </div>\n'
        '            <div class="hidden md:flex items-center space-x-6">\n'
        '                <a href="index.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">\n'
        '                    <i class="fa fa-home mr-1"></i> 首页\n'
        '                </a>\n'
        '                <a href="about.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">\n'
        '                    <i class="fa fa-info-circle mr-1"></i> 关于我们\n'
        '                </a>\n'
        '                <a href="privacy.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">\n'
        '                    <i class="fa fa-shield mr-1"></i> 隐私政策\n'
        '                </a>\n'
        '            </div>\n'
        '            <div class="md:hidden">\n'
        '                <button id="mobile-menu-toggle" class="text-white hover:text-nba-gold transition-colors duration-300">\n'
        '                    <i class="fa fa-bars text-xl"></i>\n'
        '                </button>\n'
        '            </div>\n'
        '        </div>\n'
    )
    rebuilt = opening + content + '</nav>'
    new_html = html[:nav_open.start()] + rebuilt + html[nav_close.end():]
    # Ensure mobile menu block exists just after nav
    if 'id="mobile-menu"' not in new_html:
        insert_pos = new_html.find('</nav>') + len('</nav>')
        mobile = (
            '\n    <div id="mobile-menu" class="md:hidden bg-nba-purple text-white px-4 py-3 hidden">\n'
            '        <div class="flex flex-col space-y-3">\n'
            '            <a href="index.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">\n'
            '                <i class="fa fa-home mr-1"></i> 首页\n'
            '            </a>\n'
            '            <a href="about.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">\n'
            '                <i class="fa fa-info-circle mr-1"></i> 关于我们\n'
            '            </a>\n'
            '            <a href="privacy.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">\n'
            '                <i class="fa fa-shield mr-1"></i> 隐私政策\n'
            '            </a>\n'
            '        </div>\n'
            '    </div>\n'
        )
        new_html = new_html[:insert_pos] + mobile + new_html[insert_pos:]
    # Ensure toggle script exists
    new_html = inject_mobile_script(new_html)
    return new_html


def update_nav_horizontal(html):
    # Convert the right-side nav container to horizontal layout
    # Look for the first right-side <div> that contains the Home link
    m = re.search(r'(<div>)([\s\S]*?href=\"index\.html\"[\s\S]*?)</div>', html)
    if not m:
        return html
    # If already has flex on this container, skip replacing
    opening = m.group(1)
    inner = m.group(2)
    if 'class="' in opening:
        return html
    new_right = '<div class="hidden md:flex items-center space-x-6">' + inner + '</div>'
    return html[:m.start()] + new_right + html[m.end():]


def inject_mobile_menu(html):
    # Only add if not present
    if 'id="mobile-menu-toggle"' in html:
        return html
    # Find right-side nav again to extract links for mobile menu
    m = re.search(r'(<div[^>]*class=\"hidden md:flex[^"]*\"[^>]*>)([\s\S]*?)</div>', html)
    if not m:
        m = re.search(r'(<div>)([\s\S]*?href=\"index\.html\"[\s\S]*?)</div>', html)
    if not m:
        return html
    right_div_end = m.end()
    links_html = m.group(2)
    # Build mobile toggle button after right div
    toggle = ('\n            <div class="md:hidden">\n'
              '                <button id="mobile-menu-toggle" class="text-white hover:text-nba-gold transition-colors duration-300">\n'
              '                    <i class="fa fa-bars text-xl"></i>\n'
              '                </button>\n'
              '            </div>')
    html = html[:right_div_end] + toggle + html[right_div_end:]
    # Build mobile menu container after nav closing
    nav_match = re.search(r'(</nav>)', html)
    if not nav_match:
        return html
    # Extract only anchors and wrap vertically
    # Ensure anchors are absolute as in desktop
    mobile_menu = ('\n    <div id="mobile-menu" class="md:hidden bg-nba-purple text-white px-4 py-3 hidden">\n'
                   '        <div class="flex flex-col space-y-3">\n'
                   '            ' + links_html + '\n'
                   '        </div>\n'
                   '    </div>')
    return html[:nav_match.end()] + mobile_menu + html[nav_match.end():]


def inject_mobile_script(html):
    if 'mobile-menu-toggle' in html and 'toggleMobileMenu' in html:
        return html
    script = ('\n<script>\n'
              'function toggleMobileMenu(){\n'
              '  var btn=document.getElementById("mobile-menu-toggle");\n'
              '  var menu=document.getElementById("mobile-menu");\n'
              '  if(!btn||!menu) return;\n'
              '  menu.classList.toggle("hidden");\n'
              '}\n'
              'document.addEventListener("DOMContentLoaded",function(){\n'
              '  var btn=document.getElementById("mobile-menu-toggle");\n'
              '  if(btn){ btn.addEventListener("click", toggleMobileMenu); }\n'
              '});\n'
              '</script>\n')
    # insert before </body>
    body_end = html.rfind('</body>')
    if body_end == -1:
        return html
    return html[:body_end] + script + html[body_end:]


def force_mobile_nav(html):
    # Find the nav container row
    nav_row = re.search(r'(<div class=\"container[^>]*>)([\s\S]*?)(</div>\s*</nav>)', html)
    if not nav_row:
        return html
    head, content, tail = nav_row.group(1), nav_row.group(2), nav_row.group(3)
    # Find the first right-side <div> following the brand block
    parts = content.split('</div>', 1)
    if len(parts) != 2:
        return html
    left_block = parts[0] + '</div>'
    right_and_rest = parts[1]
    # Ensure right starts with <div>
    if not right_and_rest.lstrip().startswith('<div'):
        return html
    # Replace first '<div>' with responsive class if not already present
    right_replaced = re.sub(r'^\s*<div>', '<div class="hidden md:flex items-center space-x-6">', right_and_rest, count=1)
    new_content = left_block + right_replaced
    new_html = html[:nav_row.start()] + head + new_content + tail + html[nav_row.end():]
    # Ensure hamburger and mobile menu exist
    new_html = inject_mobile_menu(new_html)
    new_html = inject_mobile_script(new_html)
    return new_html


def main():
    json_path = os.path.join(ROOT_DIR, 'nba.json')
    data = json.loads(read_text(json_path))
    updated = 0
    missing_files = []
    # maps for related
    id_to_item = {}
    for it in data:
        try:
            iid = int(it.get('id'))
            id_to_item[iid] = it
        except Exception:
            continue
    for item in data:
        local_link = item.get('localLink')
        if not local_link:
            continue
        html_path = os.path.join(ROOT_DIR, local_link)
        if not os.path.isfile(html_path):
            missing_files.append(local_link)
            continue
        detail = item.get('detail')
        title = item.get('title', '')
        if not detail:
            continue
        html = read_text(html_path)
        new_html = update_content_div(html, detail, title, local_link)
        new_html = update_hero_image(new_html, title)
        new_html = update_related_grid(new_html, item, id_to_item)
        new_html = update_nav_links(new_html)
        footer = extract_index_footer()
        if footer:
            new_html = replace_footer(new_html, footer)
        new_html = update_nav_horizontal(new_html)
        new_html = inject_mobile_menu(new_html)
        new_html = inject_mobile_script(new_html)
        new_html = force_mobile_nav(new_html)
        # Replace nav with standard mobile-friendly block for robustness (skip known proper pages)
        if local_link not in ('index.html','about.html','privacy.html'):
            new_html = replace_nav_block(new_html)
        if new_html != html:
            write_text(html_path, new_html)
            updated += 1

    print("Updated files: {}".format(updated))
    if missing_files:
        print("Missing html files:", ", ".join(missing_files))


if __name__ == '__main__':
    main()


