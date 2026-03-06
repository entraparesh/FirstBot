from flask import Flask, render_template, request,redirect, session
import requests
import csv


import json

with open("complaints.json") as f:
    complaints_db = json.load(f)

app = Flask(__name__)
app.secret_key = "indiayurveda"


dosha_map = {
    "allergic cold": "Kapha",
    "cough": "Kapha",
    "sinus": "Kapha",
    "fever": "Pitta",
    "acidity": "Pitta",
    "burning": "Pitta",
    "joint pain": "Vata",
    "gas": "Vata",
    "constipation": "Vata"
}

OLLAMA_URL = "http://localhost:11434/api/generate"

# LOGIN PAGE
@app.route("/")
def login_page():
    return render_template("login.html")

# LOGIN SUBMIT
@app.route("/login", methods=["POST"])
def login():

    user_type = request.form.get("user_type")
    email = request.form.get("email")

    session["user_type"] = user_type
    session["email"] = email
    # Save to CSV file
    with open("users.csv", "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([user_type, email])


        return redirect("/prescription")

# MAIN PAGE
@app.route("/prescription")
def prescription():

    if "email" not in session:
        return redirect("/")

    return render_template("index.html")

@app.route("/suggest")
def suggest():

    q = request.args.get("q","").lower()

    result = [c for c in complaints_db if q in c.lower()]

    return result[:10]

@app.route("/chat", methods=["POST"])
def chat():

    data = request.json
    complaints = data.get("complaints")

    complaint_text = ", ".join(complaints)

    patAge = data.get("Age")


    currSeason = data.get("Season")

    


    prompt = f"""
You are an expert Ayurvedic Vaidya.

User complaints: {complaint_text}

User Age : {patAge}

Current season : {currSeason}

User may have multiple complaints. Analyse them together according to Ayurvedic principles (Dosha imbalance) and suggest remedies that are beneficial for all the complaints.

Rules:
- Give exactly 4 Ayurvedic home remedies
- Each remedy must be one line
- Use only simple household ingredients
- No explanation
- Output must be strictly in Marathi
- Do not include English words
- Do not add extra text
- Do not use any English words in response.
- Output strictly in Marathi.
- Identify the dominant Dosha imbalance (Vata, Pitta, Kapha) using complaints and create section for showing dosha on top of remedies

Format:

1.
2.
3.
4.
"""
    
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "gemma3:4b",
            "prompt": prompt,
            "stream": False
        }
    )

    result = response.json()["response"]

    

    return result


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)