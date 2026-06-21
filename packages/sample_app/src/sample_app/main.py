import secrets
import uuid
from datetime import UTC, datetime
from flask import Flask, render_template
from sample_app.settings import settings

app = Flask(__name__, template_folder=str(settings.TEMPLATES_PATH))

@app.route("/")
def index():
    return render_template(
        "index.html",
        uuid=str(uuid.uuid4()),
        color=f"#{secrets.token_hex(nbytes=3)}",
        started_at=datetime.now(UTC).astimezone().strftime(format="%d/%m/%Y %H:%M:%S")
    )

def main():
    app.run(host="0.0.0.0", port=3000)

if __name__ == "__main__":
    main()
