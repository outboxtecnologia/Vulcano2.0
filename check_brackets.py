import glob

for f in glob.glob('frontend/src/*.jsx'):
    t = open(f, encoding='utf8').read()
    if t.count('[') != t.count(']'):
        print(f'{f}: Bracket mismatch! [:{t.count("[")} ]:{t.count("]")}')
    if t.count('{') != t.count('}'):
        print(f'{f}: Brace mismatch! {{:{t.count("{")} }}:{t.count("}")}')
    if t.count('(') != t.count(')'):
        print(f'{f}: Parenthesis mismatch! (:{t.count("(")} ):{t.count(")")}')
