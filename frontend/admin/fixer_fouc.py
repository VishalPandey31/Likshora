import os
import re

target_dir = r"c:\Users\Vishal\Downloads\Likshora\Likshora\frontend\admin"
inject_script = """
  <!-- Anti-FOUC Blocking Auth Guard -->
  <script>
    if (window.location.pathname.includes("/admin") && !window.location.pathname.includes("login")) {
      const session = localStorage.getItem("rv_admin_session");
      if (!session || session === "null") {
        window.location.replace("/admin/pages/login");
      }
    }
  </script>
"""

count = 0
for root, dirs, files in os.walk(target_dir):
    for filename in files:
        if filename.endswith(".html"):
            filepath = os.path.join(root, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Remove previous strict FOUC guard if present
            if "<!-- Anti-FOUC Blocking Auth Guard -->" in content:
                # Regex to cleanly remove the whole script block
                content = re.sub(r' *<!-- Anti-FOUC Blocking Auth Guard -->\s*<script>\s*if.*?</script>\s*', '', content, flags=re.DOTALL)

            content = content.replace("</head>", inject_script.strip("\n") + "\n</head>")
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            count += 1
                
print(f"Updated FOUC guard in {count} files.")
