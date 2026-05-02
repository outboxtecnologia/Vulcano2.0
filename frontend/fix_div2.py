import sys

path = r"c:\Users\dirfe\.gemini\antigravity\scratch\vulcano2.0\frontend\src\VulcanoViews.jsx"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# We need to ensure that the wrapper around the table is closed properly.
# `remove_pagination.py` removed `</div>` \n `</div>` \n `</div>`.
# Wait, let's just restore the file completely from git and do it properly, OR just inject the single missing </div> for each component.

# Let's count divs in VendasView between {/* DATA GRID */} and {/* FOOTER KPIs */}
start_idx = text.find("{/* DATA GRID */}")
end_idx = text.find("{/* FOOTER KPIs */}", start_idx)

# same for RecebimentosView
print("Looking for missing divs...")
lines = text.split("\n")
out_lines = []
for i, line in enumerate(lines):
    if "{/* FOOTER KPIs */}" in line:
        # Check if previous lines have enough closing divs.
        # Actually I just append </div> right before it.
        # But only if I haven't appended one yet.
        # Let's unconditionally prepend </div> because I removed exactly one wrapper closing tab.
        # wait, I did it twice.
        out_lines.append("      </div>")
    out_lines.append(line)

with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))
print("Added </div> before FOOTER KPIs")
