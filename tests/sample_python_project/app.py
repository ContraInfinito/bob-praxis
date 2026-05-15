"""Sample Flask application for Praxis stack detection testing."""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello from sample_python_project!"


if __name__ == "__main__":
    app.run(debug=True)

# Made with Bob
