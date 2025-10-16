# NBA冷门知识点HTML文件批量更新解决方案

## 问题描述
需要将项目中 `nba_1.html` 到 `nba_153.html` 中的"相关冷门知识点"部分的 `<a>` 标签的 `href` 属性修改为 `nba.json` 中对应的 `localLink` 值，并更新文字和图片。

## 修改逻辑
1. 当前页面在 `nba.json` 中的 `localLink` 值在 `nba.json` 位置下面的三个数据显示在"相关冷门知识点"
2. 文字和链接也要修改为对应的标题和链接
3. 图片也需要修改，使用基于标题生成的图片URL

## 数据结构分析
`nba.json` 包含153条数据，每条数据包含：
- `id`: 唯一标识符 (1-153)
- `title`: 知识点标题
- `localLink`: 对应的HTML文件名 (如 "nba_1.html")
- `link`: 原始链接

## 解决方案

### 方案1：使用Python脚本（推荐）

创建一个Python脚本来批量处理所有文件：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import hashlib

def load_nba_data():
    with open('nba.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_image_url(title):
    """根据标题生成图片URL"""
    hash_value = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16)
    image_id = (hash_value % 1000) + 1000
    return f"https://picsum.photos/id/{image_id}/600/300"

def find_related_facts(current_id, nba_data):
    """找到当前页面相关的三个知识点"""
    current_index = None
    for i, item in enumerate(nba_data):
        if item['id'] == current_id:
            current_index = i
            break
    
    if current_index is None:
        return []
    
    related_facts = []
    for i in range(1, 4):  # 取下面3个
        next_index = current_index + i
        if next_index < len(nba_data):
            related_facts.append(nba_data[next_index])
    
    return related_facts

def generate_related_section(related_facts):
    """生成相关知识点部分的HTML"""
    if not related_facts:
        return ""
    
    html_parts = [
        '        <!-- 相关知识点 -->',
        '        <div class="mt-12">',
        '            <h3 class="text-2xl font-bold mb-6 text-gray-800">相关冷门知识点</h3>',
        '            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">'
    ]
    
    for i, fact in enumerate(related_facts, 1):
        image_url = generate_image_url(fact['title'])
        html_parts.extend([
            f'                <!-- 相关知识点卡片{i} -->',
            f'                <a href="{fact["localLink"]}" class="block">',
            '                    <div class="bg-white rounded-lg shadow-md overflow-hidden card-hover">',
            f'                        <img src="{image_url}" alt="{fact["title"]}" class="w-full h-48 object-cover">',
            '                        <div class="p-4">',
            f'                            <h4 class="font-bold text-lg mb-2">{fact["title"]}</h4>',
            f'                            <p class="text-gray-600 text-sm">{fact["title"]}相关的冷门知识点...</p>',
            '                        </div>',
            '                    </div>',
            '                </a>'
        ])
    
    html_parts.extend([
        '            </div>',
        '        </div>'
    ])
    
    return '\n'.join(html_parts)

def update_html_file(file_path, related_facts):
    """更新HTML文件中的相关知识点部分"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 找到相关知识点部分
        pattern = r'(<!-- 相关知识点 -->.*?</div>\s*</div>\s*</main>)'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            print(f"警告: 在 {file_path} 中未找到相关知识点部分")
            return False
        
        # 生成新的相关知识点HTML
        new_related_section = generate_related_section(related_facts)
        
        # 替换内容
        new_content = content[:match.start()] + new_related_section + content[match.end():]
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
        
    except Exception as e:
        print(f"错误: 更新 {file_path} 时出错: {e}")
        return False

def main():
    """主函数"""
    # 加载NBA数据
    nba_data = load_nba_data()
    print(f"加载了 {len(nba_data)} 条NBA数据")
    
    # 处理所有HTML文件
    success_count = 0
    total_count = 0
    
    for i in range(1, 154):  # nba_1.html 到 nba_153.html
        file_path = f'nba_{i}.html'
        
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            continue
        
        total_count += 1
        
        # 找到相关知识点
        related_facts = find_related_facts(i, nba_data)
        
        if not related_facts:
            print(f"警告: 未找到 {file_path} 的相关知识点")
            continue
        
        print(f"处理 {file_path}: 找到 {len(related_facts)} 个相关知识点")
        
        # 更新HTML文件
        if update_html_file(file_path, related_facts):
            success_count += 1
            print(f"✓ 成功更新 {file_path}")
        else:
            print(f"✗ 更新失败 {file_path}")
    
    print(f"\n处理完成: {success_count}/{total_count} 个文件更新成功")

if __name__ == "__main__":
    main()
```

### 方案2：手动更新（适用于少量文件）

对于每个HTML文件，需要：

1. 找到"相关冷门知识点"部分
2. 根据当前页面的ID，从nba.json中找到下面三个数据
3. 更新三个卡片的：
   - `href` 属性为对应的 `localLink`
   - `alt` 属性为对应的 `title`
   - `src` 属性为基于 `title` 生成的图片URL
   - 标题文本为对应的 `title`
   - 描述文本为 "{title}相关的冷门知识点..."

### 示例更新

以 `nba_1.html` 为例：
- 当前页面ID为1
- 下面三个数据为ID 2、3、4
- 对应标题：斯托克顿是战斗机驾驶员、邓肯"戏耍"波波维奇、阿泰奶奶曾策划抢银行
- 对应链接：nba_2.html、nba_3.html、nba_4.html

## 图片URL生成规则

使用基于标题的哈希值生成图片ID，确保每个标题对应不同的图片：
```python
import hashlib
hash_value = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16)
image_id = (hash_value % 1000) + 1000
image_url = f"https://picsum.photos/id/{image_id}/600/300"
```

## 注意事项

1. 确保所有HTML文件都存在
2. 备份原始文件以防意外
3. 检查生成的图片URL是否有效
4. 验证更新后的链接是否正确
5. 确保Unicode字符正确处理

## 验证方法

更新完成后，可以：
1. 随机检查几个HTML文件的相关知识点部分
2. 点击链接验证跳转是否正确
3. 检查图片是否正常显示
4. 确认标题和描述文本是否正确

## 已完成的示例

- ✅ nba_1.html - 已更新相关知识点
- ✅ nba_2.html - 已更新相关知识点

剩余151个文件需要按照相同模式进行更新。
