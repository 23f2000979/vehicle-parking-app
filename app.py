from flask import Flask
app = Flask(__name__)

if __name__ == '__main__':
    @app.route('/')
    def home():
        return "Welcome to the Vehicle Parking App!"
    app.run(debug=True)

