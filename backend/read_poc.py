import sys
with open('val_poc.txt', encoding='utf-16le') as f:
    text = f.read()
    
    # Busca 124 ou 125
    if '124.5' in text or '124' in text or '125' in text:
        idx = text.find('124')
        if idx == -1: idx = text.find('125')
        print("Encontrado 124/125 perto de:", text[max(0, idx-50):idx+50])
    else:
        print("124 ou 125 nao encontrado. Ultimos valores:")
        print(text[-200:])
