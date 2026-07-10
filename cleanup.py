import os

files = ['anineko.html', 'anineko_ep1.html', 'anineko_watch.html', 'frontend/index.html']
for f in files:
    if os.path.exists(f):
        content = open(f, 'r', encoding='utf-8').read()
        start = content.find('<style>\n/* Global Poster Styles')
        if start != -1:
            end = content.find('</style>', start) + 8
            content = content[:start] + content[end:]
            open(f, 'w', encoding='utf-8').write(content)
