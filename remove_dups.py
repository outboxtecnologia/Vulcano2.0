with open(r'frontend/src/AuditoriaERPView.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Find the first and second occurrences of function TabelaMapaComparativa
matches = list(re.finditer(r'function TabelaMapaComparativa\(\{', text))

if len(matches) > 1:
    # Get the start of the first TabelaMapaComparativa
    # We want to remove the first one, which does not have the // CARD COMPARATIVO // header (or whichever)
    # The first one starts at matches[0].start()
    # The second one starts at matches[1].start()
    
    # Let's remove the first function block entirely up to the second occurrence.
    # We can use regex to find the whole function TabelaMapaComparativa block
    block_pattern = r'function TabelaMapaComparativa.*?(?=function TabelaMapa)'
    
    # The first TabelaMapaComparativa is followed by 'function TabelaMapaAgrupada' in the first attempt,
    # and then the second attempt dumped ANOTHER TabelaMapaComparativa before TabelaMapaAgrupada.
    # Let's cleanly replace all definitions of TabelaMapaComparativa to just one.
    
    text = re.sub(r'(\n\n// CARD COMPARATIVO //\n)?function TabelaMapaComparativa.*?\}\n\n// FIN CARD COMPARATIVO //\n', '', text, flags=re.DOTALL)
    text = re.sub(r'function TabelaMapaComparativa.*?\}\n\n(?=function TabelaMapa)', '', text, flags=re.DOTALL)

    with open(r'frontend/src/AuditoriaERPView.jsx', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Duplicates removed.")
else:
    print("No duplicates found.")
