import html.parser
import sys

class JSXParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        
    def handle_starttag(self, tag, attrs):
        if tag.lower() not in ['img', 'input', 'br', 'hr', 'path', 'svg', 'circle']:
            self.stack.append((tag, self.getpos()))
            
    def handle_endtag(self, tag):
        if tag.lower() not in ['img', 'input', 'br', 'hr', 'path', 'svg', 'circle']:
            if not self.stack:
                print(f"Extra closing tag: </{tag}> at {self.getpos()}")
                return
            last_tag, pos = self.stack.pop()
            if last_tag.lower() != tag.lower():
                print(f"Mismatched tag: expected </{last_tag}> but got </{tag}> at {self.getpos()}")

with open('src/App.jsx', 'r', encoding='utf-8') as f:
    code = f.read()

parser = JSXParser()
try:
    parser.feed(code)
    for tag, pos in parser.stack:
        print(f"Unclosed tag: <{tag}> at {pos}")
except Exception as e:
    print(e)
