from flask import Flask, render_template, flash, redirect, url_for
from forms import login_form
app = Flask(__name__)

app.config['SECRET_KEY'] = '9790e9651675c712d6a295af712cdef4'

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = login_form()
    if form.validate_on_submit():
        if form.username.data == 'admin' and form.password.data == 'password':
            flash('You have been logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Check username and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

if __name__ == '__main__':
    app.run(debug=True)