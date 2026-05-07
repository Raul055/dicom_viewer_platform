from flask import Flask, render_template
from forms import login_form
app = Flask(__name__)

app.config['SECRET_KEY'] = '9790e9651675c712d6a295af712cdef4'

@app.route("/")
@app.route("/login")
def login():
    form = login_form()
    return render_template('login.html', title='Login', form=form)

if __name__ == '__main__':
    app.run(debug=True)