Project Goal
Build a minimal GeoLLM chatbot web prototype that:

Accepts a natural language spatial question.

Uses Gemini API to generate a response using Chain-of-Thought (CoT)  (step-by-step GIS analysis).
MAKE A PROPER COT (SYSTEM PROPMT)
GIVE TOOLS TO USE BY LLM 
AND THIS PROJECT IS FOR ISRO (INDIA FOCUSED)
Keep the code modules like
llm (system ptomp here)
tools
app

example system prompt :
You are a GIS expert assistant helping users solve spatial problems.

Given a natural language question, generate a detailed step-by-step plan (Chain of Thought) that outlines how to solve it using basic geospatial analysis tools like buffer, intersect, difference, select by attribute, select by location, etc.

The output should be in the following format:

Step 1: ...
Step 2: ...
...

AND GIVE ONLY THE ANSWER AFTER YOU DONE FULL ANALYSIS/ NOT THE WHOLE ANALYSIS AS A PLAN
"{user_query}"
'''
(make the above one better)
add GIS realted tcode ools / libraries 
| Layer       | Tech                               |
| ----------- | ---------------------------------- |
| LLM Backend | Gemini (via `google.generativeai`) |
| Backend     | Python (Flask API)                 |
| Frontend    | HTML, CSS, JS                      |

geo-cot-chatbot/
│
├── app.py               # Flask backend to handle API request and call Gemini
├── templates/
│   └── index.html       # Chat frontend UI
└── static/
    ├── styles.css       # Optional custom CSS
    └── main.js          # JavaScript logic to call backend API


| Feature                     | Description                                                                      |
| --------------------------- | -------------------------------------------------------------------------------- |
| Input box                   | User enters a natural language query                                             |
| Gemini CoT Prompt           | chain-of-thought geospatial analysis plan                                        |
| LLM Response Handling       | Gemini returns a step-by-step plan                                               |
| Output Display              | Steps shown on a simple web UI                                                   |
| Future Expansion (Optional) | Add map support, real GIS processing (GeoPandas, QGIS, etc.)                     |


making a readme is not complasury