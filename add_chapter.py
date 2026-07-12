"""
新增章节时，自动更新全站导航。
用法: python add_chapter.py <编号> <文件名.html> <章节名>
示例: python add_chapter.py 8 微分方程.html 微分方程
"""
import sys, os, re

def add_chapter(num, filename, title):
    base = os.path.dirname(os.path.abspath(__file__))
    all_pages = ['index.html',
                 '插值与拟合.html','蒙特卡洛.html','线性回归.html',
                 '主成分与因子分析.html','时间序列.html','图与网络.html',
                 'AI与建模.html']

    sidebar_insert = f'    <a href="{filename}"><span class="tag">{num}</span>{title}</a>\n    <div class="group-label">综合专题</div>'
    nav_insert = f'  <a href="{filename}"><span class="num">{num}</span>{title}</a>\n  <div class="nav-section">综合专题</div>'

    for page in all_pages:
        path = os.path.join(base, page)
        if not os.path.exists(path):
            print(f'  SKIP (not found): {page}')
            continue

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        changed = False

        # Sidebar: insert BEFORE the "综合专题" divider line
        # Match both 4-space and tab indentation variants, and handle
        # the case where the preceding link may have class="current"
        sidebar_patterns = [
            # 4-space indent, link before group-label (no current)
            (r'(    <a href="[^"]+\.html"(?: class="current")?><span class="tag">\d+</span>[^<]+</a>\n)(    <div class="group-label">综合专题</div>)',
             rf'\1    <a href="{filename}"><span class="tag">{num}</span>{title}</a>\n\2'),
            # tab-indent variant
            (r'(\t<a href="[^"]+\.html"(?: class="current")?><span class="tag">\d+</span>[^<]+</a>\n)(\t<div class="group-label">综合专题</div>)',
             rf'\1\t<a href="{filename}"><span class="tag">{num}</span>{title}</a>\n\2'),
        ]

        for pattern, replacement in sidebar_patterns:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                content = new_content
                changed = True
                break

        # Chapter nav panel: same logic
        nav_patterns = [
            (r'(  <a href="[^"]+\.html"(?: class="current")?><span class="num">\d+</span>[^<]+</a>\n)(  <div class="nav-section">综合专题</div>)',
             rf'\1  <a href="{filename}"><span class="num">{num}</span>{title}</a>\n\2'),
        ]

        for pattern, replacement in nav_patterns:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                content = new_content
                changed = True
                break

        if changed:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'  UPDATED: {page}')
        else:
            print(f'  OK: {page}')

    print(f'\nDone! Chapter {num} ({title}) added to all pages.')

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage: python add_chapter.py <num> <file.html> <title>')
        print('Example: python add_chapter.py 8 微分方程.html 微分方程')
        sys.exit(1)
    add_chapter(sys.argv[1], sys.argv[2], sys.argv[3])
