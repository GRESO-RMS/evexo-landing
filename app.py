from flask import Flask, render_template, send_from_directory, redirect, request, jsonify
import os
import anthropic

app = Flask(__name__)

# Inizializzazione "sicura": se la chiave API manca o il file di conoscenza non si trova,
# il sito resta comunque online — solo la chat di EVY segnalerà l'errore alla singola richiesta,
# invece di far crashare l'intero sito all'avvio.
try:
    client = anthropic.Anthropic()  # legge automaticamente ANTHROPIC_API_KEY dall'ambiente
except Exception:
    client = None

EVY_SYSTEM_PROMPT_PATH = os.path.join(app.root_path, "evy", "EVY_vetrina_system_prompt.md")
try:
    with open(EVY_SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
        EVY_SYSTEM_PROMPT = f.read()
except Exception:
    EVY_SYSTEM_PROMPT = None

# Modello: Haiku è la scelta più economica, adatta a domande da vetrina.
# Se in futuro EVY dovesse gestire conversazioni più complesse, si può passare a Sonnet
# cambiando solo la stringa qui sotto.
EVY_MODEL = "claude-haiku-4-5-20251001"

MAX_MESSAGES_PER_REQUEST = 20  # limite di sicurezza sulla lunghezza della conversazione


@app.route("/api/ask-evy", methods=["POST"])
def ask_evy():
    if client is None or EVY_SYSTEM_PROMPT is None:
        return jsonify({"error": "EVY non è configurata correttamente sul server."}), 500

    data = request.get_json(force=True, silent=True) or {}
    messages = data.get("messages", [])

    if not messages or not isinstance(messages, list):
        return jsonify({"error": "missing messages"}), 400

    # tronca conversazioni troppo lunghe per contenere i costi
    messages = messages[-MAX_MESSAGES_PER_REQUEST:]

    try:
        response = client.messages.create(
            model=EVY_MODEL,
            max_tokens=400,
            system=[
                {
                    "type": "text",
                    "text": EVY_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=messages
        )
        reply = "".join(
            block.text for block in response.content if block.type == "text"
        )
        return jsonify({"reply": reply})

    except Exception as e:
        print(f"[EVY ERROR] {repr(e)}")
        return jsonify({"error": "Errore nel contattare EVY. Riprova tra poco."}), 500


@app.before_request
def enforce_canonical_domain():
    """Redirect evexo.eu (senza www) → www.evexo.eu con 301 permanente."""
    host = request.host.lower().split(":")[0]  # ignora eventuale porta in dev
    if host == "evexo.eu":
        url = request.url.replace("://evexo.eu", "://www.evexo.eu", 1)
        return redirect(url, code=301)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/robots.txt")
def robots():
    return send_from_directory(os.path.join(app.root_path, "static"), "robots.txt")

@app.route("/sitemap.xml")
def sitemap():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "sitemap.xml",
        mimetype="application/xml"
    )

if __name__ == "__main__":
    app.run(debug=True)
