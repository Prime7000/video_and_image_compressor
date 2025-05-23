from flask import Flask, render_template,request,redirect,jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/image')
def images():
    return render_template('image.html')

@app.route('/video')
def videos():
    return render_template('video.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)