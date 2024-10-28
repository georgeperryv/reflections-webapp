from flask import Flask

app = Flask(__name__)

@app.before_first_request
def setup():
    print("Running before first request.")

@app.route('/')
def index():
    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=True)
