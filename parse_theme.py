import re
import ast

def get_colors(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'colors:\s*(\{.*?\})\s*,', content, re.DOTALL)
    if not match: return {}
    color_str = match.group(1).strip()
    try:
        return ast.literal_eval(color_str)
    except Exception as e:
        print("Error evaluating", filepath, e)
        return {}

light = get_colors('stitch_export_2/stitch/dashboard_light/code.html')
dark = get_colors('stitch_export_2/stitch/dashboard_gerencial/code.html')

def hex_to_rgb(hex_code):
    hx = hex_code.lstrip('#')
    return f"{int(hx[0:2], 16)} {int(hx[2:4], 16)} {int(hx[4:6], 16)}"

css = "@layer base {\n  :root {\n"
for k, v in light.items():
    css += f"    --color-{k}: {hex_to_rgb(v)};\n"
css += "  }\n\n  .dark {\n"
for k, v in dark.items():
    if k in light: # Match light keys to keep schema symmetrical
        css += f"    --color-{k}: {hex_to_rgb(v)};\n"
css += "  }\n}\n"

with open('theme_vars.css', 'w', encoding='utf-8') as f:
    f.write(css)

tw = "      colors: {\n"
for k in light.keys():
    tw += f"        \"{k}\": \"rgb(var(--color-{k}))\",\n"
tw += "      }\n"

with open('theme_tw.txt', 'w', encoding='utf-8') as f:
    f.write(tw)

print('Success')
