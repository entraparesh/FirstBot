from flask import Flask, render_template, request, jsonify, Response
import requests
import json

app = Flask(__name__)

# -------------------------
# MEMORY STORE
MAX_HISTORY = 10   # total user+assistant messages to keep
# -------------------------

conversation = [
    {"role": "system", "content": "You are a helpful AI assistant."}
]

# -------------------------
# PROMPT BUILDER
# -------------------------

def trim_conversation():
    global conversation

    # Keep system message
    system_message = conversation[0]

    # Keep only last N messages (excluding system)
    recent_messages = conversation[1:][-MAX_HISTORY:]

    conversation = [system_message] + recent_messages

def build_prompt():
    prompt = ""
    for msg in conversation:
        if msg["role"] == "system":
            prompt += msg["content"] + "\n"
        elif msg["role"] == "user":
            prompt += "User: " + msg["content"] + "\n"
        elif msg["role"] == "assistant":
            prompt += "Assistant: " + msg["content"] + "\n"
    prompt += "Assistant:"
    return prompt

# -------------------------
# STREAMING FUNCTION
# -------------------------

def stream_from_model(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "gemma3:4b",
            "prompt": prompt,
            "stream": True
        },
        stream=True
    )

    full_reply = ""

    for chunk in response.iter_content(chunk_size=None):
        if chunk:
            data = chunk.decode("utf-8").strip()

            for line in data.split("\n"):
                if line:
                    parsed = json.loads(line)

                    if "response" in parsed:
                        token = parsed["response"]
                        full_reply += token
                        yield token

                    if parsed.get("done"):
                        conversation.append({
                            "role": "assistant",
                            "content": full_reply
                        })

# -------------------------
# ROUTES
# -------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"]

    conversation.append({
        "role": "user",
        "content": user_message
    })

    trim_conversation()   # 🔥 NEW LINE

    prompt = build_prompt()

    return Response(stream_from_model(prompt),
                    content_type="text/plain")

# -------------------------
# START SERVER
# -------------------------

if __name__ == "__main__":
    app.run(debug=True)