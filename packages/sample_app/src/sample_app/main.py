from flask import Flask, render_template
from sample_app.runtime import instance_id, background_color, started_at
from sample_app.settings import settings

app = Flask(
    __name__,
    template_folder=str(settings.resources_templates_path),
    static_folder=str(settings.resources_static_path),
    static_url_path="/static"
)

@app.route("/health")
def health():
    return "", 204

@app.route("/")
def index():
    return render_template(
        "index.html",
        instance_id=str(instance_id),
        background_color=background_color,
        started_at=started_at.astimezone().strftime(format="%d/%m/%Y %H:%M:%S")
    )

def main():
    app.run(host="0.0.0.0", port=3000)

if __name__ == "__main__":
    main()
