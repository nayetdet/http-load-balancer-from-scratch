import time
from flask import Flask, render_template, request
from sample_app.runtime import instance_id, background_color, started_at
from sample_app.settings import settings

app = Flask(__name__, template_folder=str(settings.resources_templates_path))

@app.route("/health")
def health():
    return "", 204

@app.route("/info")
def info():
    delay: float = float(request.args.get("delay", 0))
    if delay > 0:
        time.sleep(delay)

    return {
        "instance_id": str(instance_id),
        "background_color": background_color,
        "started_at": started_at.astimezone().isoformat()
    }

@app.route("/")
def index():
    return render_template(
        "index.html",
        instance_id=str(instance_id),
        background_color=background_color,
        started_at=started_at.astimezone().isoformat()
    )

def main():
    app.run(host="0.0.0.0", port=3000)

if __name__ == "__main__":
    main()
