import os, google.generativeai as genai
genai.configure(api_key='BAD_KEY')
model = genai.GenerativeModel('gemini-2.5-flash')
try:
    model.generate_content('hi')
except Exception as e:
    print("OUTPUT EXCEPTION:", e)
