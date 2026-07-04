import os

BASE_DIR = r"e:\nompyr\backend"

replace_map = {
    "from content_service.metadata.content_filter": "from content_service.metadata.content_filter",
    "import content_service.metadata.content_filter": "import content_service.metadata.content_filter",
    "from content_service.metadata.enrichment": "from content_service.metadata.enrichment",
    "import content_service.metadata.enrichment": "import content_service.metadata.enrichment",
    "from content_service.metadata.anilist": "from content_service.metadata.anilist",
    "import content_service.metadata.anilist": "import content_service.metadata.anilist",
    "from content_service.metadata.jikan": "from content_service.metadata.jikan",
    "import content_service.metadata.jikan": "import content_service.metadata.jikan",
}

def fix_imports_in_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    original_content = content
    for old_str, new_str in replace_map.items():
        content = content.replace(old_str, new_str)
        
    if content != original_content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated imports in {filepath}")

for root, dirs, files in os.walk(BASE_DIR):
    for file in files:
        if file.endswith(".py"):
            fix_imports_in_file(os.path.join(root, file))

print("Import fixing script finished.")
