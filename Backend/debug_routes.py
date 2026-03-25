import sys
import os

# Add Backend to path
sys.path.append(os.getcwd())

try:
    from main import app
    print("🚀 Verifying Auth Routes:")
    found = False
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = list(getattr(route, "methods", []))
        if "/auth/" in path:
            print(f"- {methods} {path}")
            found = True
    if not found:
        print("❌ No auth routes found!")
except Exception as e:
    print(f"❌ Error: {str(e)}")
