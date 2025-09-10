from config import *
import google.generativeai as genai

genai.configure(api_key=Gemini_api_key)  

model = genai.GenerativeModel("models/gemini-1.5-flash")

response = model.generate_content("Hello, Gemini!")
print("Answer:", response.text)