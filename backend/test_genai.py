from dotenv import load_dotenv
load_dotenv()
import os
import google.generativeai as genai

key = os.environ.get('GEMINI_API_KEY')
print(f"Key loaded: {'Yes' if key else 'No'}")
genai.configure(api_key=key)

try:
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content('hi')
    print("SUCCESS:", response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
