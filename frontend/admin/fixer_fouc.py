import os

target_dir = r"c:\Users\Vishal\Downloads\Likshora\Likshora\frontend\admin"
inject_script = """
  <!-- Anti-FOUC Blocking Auth Guard -->
  <script>
    if (window.location.pathname.includes("/admin") && !window.location.pathname.includes("login.html")) {
      const session = localStorage.getItem("rv_admin_session");
      if (!session || session === "null") {
        window.location.replace("/admin/pages/login.html");
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
            
            if "Anti-FOUC Blocking Auth Guard" not in content and "</head>" in content:
                content = content.replace("</head>", inject_script + "</head>")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                count += 1
                
print(f"Injected FOUC guard into {count} files.")
