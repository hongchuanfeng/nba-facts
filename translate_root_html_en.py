#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import glob


def translate_html_content(content):
    """
    Perform deterministic UI text translations and attribute fixes only.
    This avoids changing content under cn/ and keeps structure/spacing intact.
    """
    # 1) html lang -> en (common variants)
    content = re.sub(u"(<html\s+[^>]*?lang=\")zh(?:-CN)?(\")", u"\\1en\\2", content, flags=re.IGNORECASE)

    # 2) Common UI phrases mapping (ordered: longer first to avoid partial collisions)
    replacements = [
        # Navigation / common labels
        (u"NBA冷门知识库", u"NBA Fun Facts"),
        (u"隐私政策", u"Privacy Policy"),
        (u"关于我们", u"About"),
        (u"首页", u"Home"),
        (u"冷门知识点", u"Fun Facts"),
        (u"冷门知识", u"Fun Facts"),
        (u"快速链接", u"Quick Links"),
        (u"知识点分类", u"Categories"),
        (u"联系我们", u"Contact Us"),
        (u"联系\u6211\u4eec", u"Contact Us"),
        (u"小贴士", u"Tip"),
        (u"搜索标题...", u"Search titles..."),
        (u"搜索", u"Search"),
        (u"加载更多", u"Load more"),
        (u"加载完成", u"All loaded"),
        (u"加载失败，重试", u"Load failed, retry"),
        (u"阅读更多", u"Read more"),
        (u"开始探索", u"Start Exploring"),
        (u"获取更多NBA冷门知识", u"Get more NBA fun facts"),
        (u"订阅我们的 newsletter，每周收到精选的NBA冷门知识点和趣闻", u"Subscribe to our newsletter for weekly curated NBA fun facts and stories"),
        (u"输入你的邮箱地址", u"Enter your email address"),
        (u"立即订阅", u"Subscribe Now"),
        (u"你的名字", u"Your name"),
        (u"你的邮箱", u"Your email"),
        (u"留言...", u"Message..."),
        (u"发送", u"Send"),
        (u"未找到匹配结果", u"No matching results found"),
        (u"球员故事", u"Player Stories"),
        (u"球员轶事", u"Player Anecdotes"),
        (u"趣味故事", u"Fun Stories"),
        (u"场外趣闻", u"Off-court Trivia"),
        (u"球员才华", u"Player Talents"),
        (u"球员往事", u"Player Past"),
        (u"知识点列表区", u"Facts"),
        (u"英雄区", u"Hero"),
        (u"关于NBA冷门知识库", u"About NBA Fun Facts"),
        (u"我们的使命", u"Our Mission"),
        (u"我们是谁", u"Who We Are"),
        (u"我们如何做", u"How We Work"),
        (u"深圳市龙华区130号", u"Longhua District, Shenzhen"),
        (u"min read", u"min read"),  # keep English unit if appears
        # Footer sentences
        (u"本网站仅供学习交流使用，与NBA官方无任何关联", u"For learning and communication only; not affiliated with the NBA"),
        (u"探索NBA不为人知的有趣故事，让你成为真正的篮球专家", u"Explore lesser-known NBA stories and become a true hoops expert"),
    ]

    # Apply literal replacements while preserving original spacing
    for zh, en in replacements:
        content = content.replace(zh, en)

    # 3) Convert a few prominent headings/descriptions in index-like pages
    content = content.replace(
        u"探索NBA不为人知的\n冷门知识点", u"Explore NBA's lesser-known fun facts"
    ).replace(
        u"探索NBA不为人知的<br>冷门知识点", u"Explore NBA's lesser-known fun facts"
    )

    # 4) Update some alt attributes containing Chinese only if they are simple labels
    content = re.sub(u'alt="首页"', u'alt="Home"', content)

    return content


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    # Collect root-level html files only
    html_files = glob.glob(os.path.join(root, '*.html'))

    if not html_files:
        print("No root-level HTML files found.")
        return

    changed = 0
    for file_path in html_files:
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            try:
                original = data.decode('utf-8')
            except Exception:
                original = data.decode('utf-8', 'ignore')
        except Exception:
            continue

        # Ensure unicode in Python 2
        if not isinstance(original, unicode):  # noqa: F821 for Py3 linters
            try:
                original = original.decode('utf-8')
            except Exception:
                original = original.decode('utf-8', 'ignore')

        updated = translate_html_content(original)
        if updated != original:
            with open(file_path, 'wb') as f:
                f.write(updated.encode('utf-8'))
            changed += 1

    print("Updated {} root HTML files.".format(changed))


if __name__ == "__main__":
    main()


