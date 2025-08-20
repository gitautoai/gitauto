import os
import tempfile
from services.webhook.screenshot_handler import find_all_html_pages

# Test the fix
with tempfile.TemporaryDirectory() as temp_dir:
    # Create Next.js App Router structure
    app_dir = os.path.join(temp_dir, "app")
    os.makedirs(os.path.join(app_dir, "about"))
    os.makedirs(os.path.join(app_dir, "products", "category"))
    
    # Create page files
    open(os.path.join(app_dir, "page.tsx"), "w").close()
    open(os.path.join(app_dir, "about", "page.tsx"), "w").close()
    open(os.path.join(app_dir, "products", "category", "page.jsx"), "w").close()
    open(os.path.join(app_dir, "layout.tsx"), "w").close()

    # Execute
    result = find_all_html_pages(temp_dir)
    
    print(f"Result: {result}")
    print(f"'/' in result: {'/' in result}")
    print(f"'/about' in result: {'/about' in result}")
    print(f"'/products/category' in result: {'/products/category' in result}")
    print(f"Test passes: {'/' in result and '/about' in result and '/products/category' in result}")