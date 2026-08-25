import os, glob

base = 'c:/Users/Vishal/Downloads/Likshora/Likshora/frontend'
htmls = glob.glob(base + '/**/*.html', recursive=True)

# also fix products.html if it misses it in case I used the wrong path earlier
for f in set(htmls):
    try:
        content = open(f, 'r', encoding='utf-8').read()
        updated = content
        
        # for product-details
        if '<script src="../../js/customer/product-details.js"></script>' in updated:
            if '<script src="../../js/api/api.js"></script>' not in updated:
                updated = updated.replace(
                    '<script src="../../js/customer/product-details.js"></script>',
                    '<script src="../../js/api/api.js"></script>\n<script src="../../js/api/product-api.js"></script>\n<script src="../../js/customer/product-details.js"></script>'
                )
                
        # for home.js
        if '<script src="js/customer/home.js"></script>' in updated:
            if '<script src="js/api/api.js"></script>' not in updated:
                updated = updated.replace(
                    '<script src="js/customer/home.js"></script>',
                    '<script src="js/api/api.js"></script>\n<script src="js/api/product-api.js"></script>\n<script src="js/customer/home.js"></script>'
                )

        if content != updated:
            open(f, 'w', encoding='utf-8').write(updated)
            print(f"Fixed {f}")
    except Exception as e:
        pass
