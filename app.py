from flask import Flask, render_template, send_from_directory, redirect, request
import os

app = Flask(__name__)

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
