from dotenv import load_dotenv
load_dotenv()
import os
import google.generativeai as genai

key = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=key)

try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content('hi')
    print("SUCCESS:", response.text)
except Exception as e:
    print('ERROR MSG:', e)
