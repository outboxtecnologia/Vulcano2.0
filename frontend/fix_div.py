import sys

with open(r"c:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0\frontend\src\VulcanoViews.jsx", "r", encoding="utf-8") as f:
    text = f.read()

# Replace any occurrence of table wrapper lacking its closing div before Footer
text = text.replace('          </div>\n\n      {/* FOOTER KPIs */}', '          </div>\n      </div>\n\n      {/* FOOTER KPIs */}')
text = text.replace('         </div>\n\n      {/* FOOTER KPIs */}', '         </div>\n      </div>\n\n      {/* FOOTER KPIs */}')

with open(r"c:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0\frontend\src\VulcanoViews.jsx", "w", encoding="utf-8") as f:
    f.write(text)

print("fixed")
