import os

from flask import Flask, session, escape, redirect, url_for, abort, send_file
from flask import render_template
from flask import request, g

from storage import get_db, init_db
import pdfkit
from dataclasses import dataclass


@dataclass
class Resume:
    username: str
    full_name: str
    date_of_birth: str
    education: str
    skills: str
    personal_info: str


app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'))

init_db(app, app.config['DATABASE'])
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def index():
    if 'username' in session:
        # pdfkit.from_url('http://google.com', 'out.pdf', verbose=True)

        # db = get_db(app.config['DATABASE'])
        # curr_resume = db.execute(f'select * from resumes where username = \'{session["username"]}\'').fetchone()
        # pdfkit.from_string(render_template('resume.html', resume=curr_resume).strip(), 'out.pdf')

        return f'''
        <p>Logged in as %s</p>
        <p>Now you can start working on your resume in <a href="{url_for('resume')}">editor</a></p>

        <p><a href="{url_for('logout')}">log out</a>
        ''' % escape(
            session['username'])  # escape заменяет все специсимволы на безопасные (потому что можно же ломать сайты)
    return f'''
    <p>You are not logged in</p>
    <p>Do you want to <a href="{url_for('login')}">log in</a> or <a href="{url_for('register')}">create a new account</a>?</p>
    '''


@app.route('/register', methods=['POST', 'GET'])
def register():
    curr_error = None
    if request.method == 'POST':
        new_username = request.form['username'].lower()
        new_password = request.form['password']
        new_name = request.form['name']
        if len(new_username) * len(new_password) * len(new_name) != 0:
            db = get_db(app.config['DATABASE'])
            try:
                db.execute(
                    'insert into users (username, password, name) values (?, ?, ?)',
                    [new_username, new_password, new_name]
                )
                db.commit()

                db.execute(
                    'insert into resumes (username, full_name) values (?, ?)',
                    [new_username, new_name]
                )
                db.commit()

                session['username'] = new_username
                session['password'] = new_password
                session['logged_in'] = True
                return redirect(url_for('index'))

            except g.sqlite_db.IntegrityError:
                curr_error = "Non unique username"
        else:
            curr_error = "Empty slots"

    return render_template('register.html', error=curr_error)


@app.route('/login', methods=['POST', 'GET'])
def login():
    curr_error = None
    if request.method == 'POST':
        curr_username = request.form['username'].lower()
        curr_password = request.form['password']
        if len(curr_username) * len(curr_password) != 0:
            db = get_db(app.config['DATABASE'])

            query = f'select username, password from users where username = \'{curr_username}\''
            found_user = db.execute(query).fetchone()
            if not found_user:
                curr_error = "User not found"
            else:
                if found_user['password'] != curr_password:
                    curr_error = "Wrong password"
                else:
                    session['username'] = curr_username
                    session['password'] = curr_password
                    session['logged_in'] = True
                    return redirect(url_for('index'))
        else:
            curr_error = "Empty slots"
    return render_template('login.html', error=curr_error)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/resume', methods=['GET', 'POST'])
def resume():
    if not session.get('logged_in'):
        abort(401)

    db = get_db(app.config['DATABASE'])

    query = f'select * from resumes where username = \'{session["username"]}\''
    curr_resume = db.execute(query).fetchone()

    if "save_button" in request.form:
        db.execute(
            'replace into resumes (username, full_name, date_of_birth, education, skills, personal_info) values (?, ?, ?, ?, ?, ?)',
            [session["username"], request.form.get('full_name', curr_resume["full_name"]),
             request.form.get('date_of_birth', curr_resume["date_of_birth"]),
             request.form.get('education', curr_resume["education"]),
             request.form.get('skills', curr_resume["skills"]),
             request.form.get('personal_info', curr_resume["personal_info"])])
        db.commit()
        render_resume = db.execute(f'select * from resumes where username = \'{session["username"]}\'').fetchone()

    if "download_button" in request.form:
        # сырую дата строчку пдф есть не захотел (why....), так что я сделала класс

        tmp_resume = db.execute(f'select * from resumes where username = \'{session["username"]}\'').fetchone()
        render_resume = Resume(username=tmp_resume["username"], full_name=tmp_resume["full_name"],
                               date_of_birth=tmp_resume["date_of_birth"],
                               education=tmp_resume["education"], skills=tmp_resume["skills"],
                               personal_info=tmp_resume["personal_info"])

        return redirect(url_for('download', down_resume=render_resume))

    else:
        render_resume = db.execute(f'select * from resumes where username = \'{session["username"]}\'').fetchone()

    return render_template('resume.html', resume=render_resume)


@app.route('/download/<down_resume>', methods=['GET', 'POST'])
def download(down_resume):
    if not session.get('logged_in'):
        abort(401)
    down_resume = eval(down_resume)
    pdfkit.from_string(render_template('resume.html', resume=down_resume), 'out.pdf', verbose=True, )
    return send_file(
        path_or_file='out.pdf',
        download_name='resume.pdf',
        as_attachment=True
    )


app.run(debug=True)
