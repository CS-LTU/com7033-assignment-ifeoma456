#from flask import Flask
from gettext import install
import flask

#app = Flask(__name__)


    




#@app.route('/')
#def home():
    #return '''
       # <h1> Welcome to Flask in jupyter! </h1>
       # <p> This is a Simple Webpage Served using Flask inside Jupyter.</p>
        # <a href=" /about">Go to About Page and the dashboard. </a>
        # '''
#@app.route('/about')
#def about():
    #return'''
       # <h1>About This Web App</h1>
        #<p>This Page was generated using Flask with aJupyter notebook. It's a simple example to show Flask routing.</p>
       # <a href="/">Go back Home</a>
       # '''

#if __name__ == '__main__':
  #  app.run(debug=True)


def start_app():
    print('Secure Patient App Started Successfully!')
from app import start_app
if __name__ == '__main__':
    start_app()
from setuptools import setup, find_packages
setup(
    name='secure_patient_app',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'flask',
    ],
    entry_points={
        'console_scripts': [
            'start-secure-patient-app=run:start_app',
        ],
    },  
)     

from flask import Flask     
def create_app():
    app = Flask(__name__)
    @app.route('/')
    def home():
        return 'Hello, Secure Patient App!'
    return app
from app import create_app
app = create_app()
if __name__ == '__main__':
    app.run(debug=True)