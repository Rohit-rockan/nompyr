import os

with open('mobile-override.css', 'r') as f:
    css = f.read()

style_block = f"<style>\n{css}\n</style>"

files = ['anineko.html', 'anineko_ep1.html', 'anineko_watch.html', 'frontend/index.html']

for file_path in files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace links with inline style
        content = content.replace('<link rel="stylesheet" type="text/css" href="mobile-override.css" />', style_block)
        content = content.replace('<link rel="stylesheet" type="text/css" href="/mobile-override.css" />', style_block)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Updated {file_path}")
    except Exception as e:
        print(f"Failed to update {file_path}: {e}")
