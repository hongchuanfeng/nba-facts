import re

# 读取start.md文件
with open('start.md', 'r', encoding='utf-8') as f:
    content = f.read()

# 定义12位明星的数据
stars = [
    {
        'num': 1,
        'name': 'Michael Jordan',
        'name_short': 'Jordan',
        'title': 'Jordan Set the Lowest Score in Three-Point Contest History',
        'image_id': '893',
        'related': [2, 11, 10]
    },
    {
        'num': 2,
        'name': 'LeBron James',
        'name_short': 'LeBron',
        'title': 'LeBron Spends Millions of Dollars Annually on Body Maintenance',
        'image_id': '2544',
        'related': [1, 3, 11]
    },
    {
        'num': 3,
        'name': 'Kareem Abdul-Jabbar',
        'name_short': 'Abdul-Jabbar',
        'title': 'Abdul-Jabbar is the NBA\'s All-Time Scoring Leader but Never Won a Dunk Contest',
        'image_id': '76003',
        'related': [4, 2, 6]
    },
    {
        'num': 4,
        'name': 'Magic Johnson',
        'name_short': 'Magic',
        'title': 'Magic Won the NBA Championship and Finals MVP at Age 20',
        'image_id': '77142',
        'related': [3, 9, 5]
    },
    {
        'num': 5,
        'name': 'Bill Russell',
        'name_short': 'Russell',
        'title': 'Russell Has 11 Championship Rings but Never Won a Scoring Title',
        'image_id': '78049',
        'related': [6, 4, 9]
    },
    {
        'num': 6,
        'name': 'Wilt Chamberlain',
        'name_short': 'Chamberlain',
        'title': 'Chamberlain\'s 100-Point Game Was Actually Played in a Small Arena',
        'image_id': '76375',
        'related': [5, 3, 12]
    },
    {
        'num': 7,
        'name': 'Tim Duncan',
        'name_short': 'Duncan',
        'title': 'Duncan Was Ejected for Laughing on the Bench',
        'image_id': '1495',
        'related': [8, 11, 10]
    },
    {
        'num': 8,
        'name': 'Shaquille O\'Neal',
        'name_short': 'O\'Neal',
        'title': 'O\'Neal Released Rap Albums',
        'image_id': '406',
        'related': [7, 11, 12]
    },
    {
        'num': 9,
        'name': 'Larry Bird',
        'name_short': 'Bird',
        'title': 'Bird is the Only Player to Win Both Preseason MVP and Finals MVP',
        'image_id': '1449',
        'related': [4, 5, 1]
    },
    {
        'num': 10,
        'name': 'Stephen Curry',
        'name_short': 'Curry',
        'title': 'Curry\'s Shooting Form Was Once Criticized',
        'image_id': '201939',
        'related': [11, 1, 7]
    },
    {
        'num': 11,
        'name': 'Kobe Bryant',
        'name_short': 'Kobe',
        'title': 'Kobe\'s First and Last NBA Points Were Both Free Throws',
        'image_id': '977',
        'related': [1, 2, 8]
    },
    {
        'num': 12,
        'name': 'Hakeem Olajuwon',
        'name_short': 'Olajuwon',
        'title': 'Olajuwon Was the First International No. 1 Overall Pick in NBA History',
        'image_id': '165',
        'related': [6, 8, 3]
    }
]

# 提取每个明星的内容
def extract_star_content(num):
    star_name = stars[num-1]['name']
    pattern = rf'## {num}\. {re.escape(star_name)}.*?(?=## \d+\.|## Summary|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        text = match.group(0)
        # 提取Fun Fact描述
        fun_fact_match = re.search(r'\*\*Fun Fact:.*?\*\*\s*\n\n(.*?)(?=\*\*More Details:|\Z)', text, re.DOTALL)
        fun_fact = fun_fact_match.group(1).strip() if fun_fact_match else ''
        # 提取More Details列表
        details_match = re.search(r'\*\*More Details:\*\*\s*\n((?:- .*?\n)+)', text, re.DOTALL)
        details = details_match.group(1).strip() if details_match else ''
        return fun_fact, details
    return '', ''

# 生成HTML模板
def generate_html(star):
    fun_fact, details = extract_star_content(star['num'])
    
    # 处理details，转换为HTML列表
    details_html = ''
    if details:
        details_list = [d.strip('- ').strip() for d in details.split('\n') if d.strip().startswith('-')]
        details_html = '\n'.join([f'                        <li>{detail}</li>' for detail in details_list if detail])
    
    # 生成相关链接
    related_html = ''
    for rel_num in star['related']:
        rel_star = stars[rel_num-1]
        related_html += f'''
                <a href="start_{rel_num}.html" class="block">
                    <div class="bg-white rounded-lg shadow-md overflow-hidden card-hover">
                        <img src="https://cdn.nba.com/headshots/nba/latest/1040x760/{rel_star['image_id']}.png" alt="{rel_star['name']}" class="w-full h-48 object-cover" onerror="this.onerror=null;this.src='https://picsum.photos/id/{rel_star['image_id']}/600/300';">
                        <div class="p-4">
                            <h4 class="font-bold text-lg mb-2">{rel_star['title'][:50]}...</h4>
                            <p class="text-gray-600 text-sm">{rel_star['name']} - {rel_star['title'][:60]}...</p>
                        </div>
                    </div>
                </a>'''
    
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{star['title']} - NBA Fun Facts</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css" rel="stylesheet">
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        nba: {{
                            purple: '#552583',
                            gold: '#FDB927',
                            dark: '#171717',
                            light: '#F5F5F5'
                        }}
                    }},
                    fontFamily: {{
                        sans: ['Inter', 'system-ui', 'sans-serif'],
                    }},
                }}
            }}
        }}
    </script>
    <style type="text/tailwindcss">
        @layer utilities {{
            .text-shadow {{
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            }}
            .card-hover {{
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }}
            .card-hover:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            }}
        }}
    </style>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-8WF0S87W7F"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', 'G-8WF0S87W7F');
</script>
    <link rel="icon" href="favicon.ico">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7274710287377352"
     crossorigin="anonymous"></script>
</head>
<body class="bg-gray-100 font-sans">
    <!-- 导航栏 -->
    <nav class="bg-nba-purple text-white shadow-md">
        <div class="container mx-auto px-4 py-3 flex justify-between items-center">
            <div class="flex items-center space-x-2">
                <i class="fa fa-basketball-ball text-2xl text-nba-gold"></i>
                <h1 class="text-xl font-bold">NBA Fun Facts</h1>
            </div>
            <div class="hidden md:flex items-center space-x-6">
                <a href="index.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">
                    <i class="fa fa-home mr-1"></i> Home
                </a>
                <a href="about.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">
                    <i class="fa fa-info-circle mr-1"></i> About
                </a>
                <a href="privacy.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">
                    <i class="fa fa-shield mr-1"></i> Privacy Policy
                </a>
            </div>
            <div class="md:hidden">
                <button id="mobile-menu-toggle" class="text-white hover:text-nba-gold transition-colors duration-300">
                    <i class="fa fa-bars text-xl"></i>
                </button>
            </div>
        </div>
</nav>

    <div id="mobile-menu" class="md:hidden bg-nba-purple text-white px-4 py-3 hidden">
        <div class="flex flex-col space-y-3">
            <a href="index.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">
                <i class="fa fa-home mr-1"></i> Home
            </a>
            <a href="about.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">
                <i class="fa fa-info-circle mr-1"></i> About
            </a>
            <a href="privacy.html" class="text-white hover:text-nba-gold transition-colors duration-300 flex items-center">
                <i class="fa fa-shield mr-1"></i> Privacy Policy
            </a>
        </div>
    </div>

    <!-- 主内容区 -->
    <main class="container mx-auto px-4 py-8">
        <div class="max-w-4xl mx-auto bg-white rounded-lg shadow-lg overflow-hidden">
            <!-- 标题区 -->
            <div class="relative h-64 md:h-80">
                <img src="https://cdn.nba.com/headshots/nba/latest/1040x760/{star['image_id']}.png" alt="{star['name']}" class="w-full h-full object-cover" onerror="this.onerror=null;this.src='https://picsum.photos/id/{star['image_id']}/1200/400';">
                <div class="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent flex items-end">
                    <h2 class="text-2xl md:text-4xl font-bold text-white p-6 text-shadow">{star['title']}</h2>
                </div>
            </div>
            
            <!-- 内容区 -->
            <div class="p-6 md:p-8">
                <!-- 徽章 + 阅读时长 -->
                <div class="flex items-center gap-2 mb-6 text-sm">
                    <span class="px-3 py-1 rounded-full bg-nba-purple/10 text-nba-purple">{star['name']}</span>
                    <span class="px-3 py-1 rounded-full bg-nba-gold/10 text-nba-gold">Fun Fact</span>
                    <span class="ml-auto text-gray-500 flex items-center"><i class="fa fa-clock-o mr-1"></i> 5 min read</span>
                </div>

                <!-- 渐变分隔线 -->
                <div class="relative mb-6">
                    <div class="h-1 w-24 bg-gradient-to-r from-nba-purple to-nba-gold rounded"></div>
                </div>

                <!-- 正文分段 -->
                <div class="prose lg:prose-xl max-w-none">
                    <p class="text-lg leading-relaxed whitespace-pre-line">{fun_fact}</p>
                    
                    <h3 class="text-2xl font-bold mt-8 mb-4 text-gray-800">More Details</h3>
                    <ul class="list-disc list-inside space-y-2 text-lg leading-relaxed text-gray-700">
{details_html}
                    </ul>
                </div>

                <!-- 侧栏引述与提示 -->
                <div class="mt-8 grid md:grid-cols-5 gap-6 items-start">
                    <div class="md:col-span-3">
                        <div class="bg-nba-light/60 border border-gray-100 rounded-lg p-4">
                            <div class="flex items-center text-nba-purple font-medium mb-2"><i class="fa fa-lightbulb-o mr-2"></i>Tip</div>
                            <p class="text-gray-700 leading-relaxed">These fun facts reveal the human side of NBA legends and their unique journeys.</p>
                        </div>
                    </div>
                    <div class="md:col-span-2">
                        <blockquote class="rounded-lg bg-gradient-to-br from-nba-purple/10 to-nba-gold/10 border-l-4 border-nba-purple p-4 italic text-gray-700">
                            "{star['name']}'s story shows that greatness comes in many forms, each with its own unique path."
                        </blockquote>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 相关知识点 -->
        <div class="mt-12">
            <h3 class="text-2xl font-bold mb-6 text-gray-800">Related Fun Facts</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
{related_html}
            </div>
        </div>
    </main>

    <!-- 页脚 -->
    <footer class="bg-nba-dark text-white pt-16 pb-8">
        <div class="container mx-auto px-4">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
                <div>
                    <div class="flex items-center space-x-2 mb-4">
                        <i class="fa fa-basketball-ball text-2xl text-nba-gold"></i>
                        <span class="font-bold text-xl">NBA Fun Facts</span>
                    </div>
                    <p class="text-gray-400 mb-4">Explore lesser-known NBA stories and become a true hoops expert</p>
                    <div class="flex space-x-4">
                        <a href="#" class="text-gray-400 hover:text-nba-gold transition-colors duration-300">
                            <i class="fa fa-facebook"></i>
                        </a>
                        <a href="#" class="text-gray-400 hover:text-nba-gold transition-colors duration-300">
                            <i class="fa fa-twitter"></i>
                        </a>
                        <a href="#" class="text-gray-400 hover:text-nba-gold transition-colors duration-300">
                            <i class="fa fa-instagram"></i>
                        </a>
                        <a href="#" class="text-gray-400 hover:text-nba-gold transition-colors duration-300">
                            <i class="fa fa-youtube-play"></i>
                        </a>
                    </div>
                </div>
                
                <div>
                    <h4 class="font-bold text-lg mb-4">Quick Links</h4>
                    <ul class="space-y-2">
                        <li><a href="index.html" class="text-gray-400 hover:text-nba-gold transition-colors duration-300">Home</a></li>
                        <li><a href="index.html#facts" class="text-gray-400 hover:text-nba-gold transition-colors duration-300">Fun Facts</a></li>
                        <li><a href="about.html" class="text-gray-400 hover:text-nba-gold transition-colors duration-300">About</a></li>
                        <li><a href="#" class="text-gray-400 hover:text-nba-gold transition-colors duration-300">Contact Us</a></li>
                    </ul>
                </div>
                
                <div>
                    <h4 class="font-bold text-lg mb-4">Categories</h4>
                    <ul class="space-y-2">
                        <li><a href="#" class="text-gray-400 hover:text-nba-gold transition-colors duration-300">Player Stories</a></li>
                        <li><a href="#" class="text-gray-400 hover:text-nba-gold transition-colors duration-300">Team History</a></li>
                        <li><a href="#" class="text-gray-400 hover:text-nba-gold transition-colors duration-300">Stats Trivia</a></li>
                        <li><a href="#" class="text-gray-400 hover:text-nba-gold transition-colors duration-300">Rules Fun Facts</a></li>
                    </ul>
                </div>
                
                <div>
                    <h4 class="font-bold text-lg mb-4">Contact Us</h4>
                    <ul class="space-y-2">
                        <li class="flex items-center text-gray-400">
                            <i class="fa fa-envelope mr-2"></i> hcf@foxmail.com
                        </li>
                        <li class="flex items-center text-gray-400">
                            <i class="fa fa-twitter mr-2"></i> @nbacoldfacts
                        </li>
                        <li class="flex items-center text-gray-400">
                            <i class="fa fa-map-marker mr-2"></i> Longhua District, Shenzhen
                        </li>
                    </ul>
                </div>
            </div>
            
            <div class="border-t border-gray-700 pt-8 text-center text-gray-400 text-sm">
                <p>© 2023 NBA Fun Facts - For learning and communication only; not affiliated with the NBA</p>
            </div>
        </div>
    </footer>

<script>
function toggleMobileMenu(){{
  var btn=document.getElementById("mobile-menu-toggle");
  var menu=document.getElementById("mobile-menu");
  if(!btn||!menu) return;
  menu.classList.toggle("hidden");
}}
document.addEventListener("DOMContentLoaded",function(){{
  var btn=document.getElementById("mobile-menu-toggle");
  if(btn){{ btn.addEventListener("click", toggleMobileMenu); }}
}});
</script>
</body>
</html>'''
    return html_template

# 生成所有页面（4-12，因为1-3已经手动创建）
for star in stars[3:]:
    html = generate_html(star)
    filename = f"start_{star['num']}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Generated {filename}')

print('All pages generated successfully!')


