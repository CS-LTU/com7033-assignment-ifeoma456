from flask import Flask
import flask

app = Flask(__name__)


    




@app.route('/')
def home():
    return '''
        <h1> Welcome to Flask in jupyter! </h1>
        <p> This is a Simple Webpage Served using Flask inside Jupyter.</p>
        <a href=" /about">Go to About Page</a>
        '''
@app.route('/about')
def about():
    return'''
        <h1>About This Web App</h1>
        <p>This Page was generated using Flask with aJupyter notebook. It's a simple example to show Flask routing.</p>
        <a href="/">Go back Home</a>
        '''

if __name__ == '__main__':
    app.run(debug=True)



    