from bs4 import BeautifulSoup
import re

def clean_element(el):
    # Remove scripts, styles
    for tag in el.find_all(['script', 'style', 'svg', 'path']):
        tag.decompose()
        
    # Remove comments
    for comment in el.find_all(string=lambda text: isinstance(text, str) and text.strip().startswith('<!--')):
        comment.extract()

with open('rendered_tributos_dom.html', 'r', encoding='utf-8', errors='ignore') as f:
    soup = BeautifulSoup(f, 'html.parser')

main_content = soup.find('div', id='root')
if not main_content:
    main_content = soup.find('body')

if main_content:
    clean_element(main_content)
    with open('tributos_review_structure.html', 'w', encoding='utf-8') as f:
        f.write(main_content.prettify())
    print("Successfully parsed and saved to tributos_review_structure.html")
else:
    print("Could not find root or body element")
