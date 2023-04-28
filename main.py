from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eureka.db'

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nick = db.Column(db.String(16), nullable=False)
    email = db.Column(db.String, nullable=False)
    name = db.Column(db.String)
    second_name = db.Column(db.String)
    about = db.Column(db.Text(500))

    def __repr__(self):
        return self.nick


@app.route('/')
def main():
    return render_template('main.html', title='Главная страница')


@app.route('/projects')
def projects():
    return render_template('projects.html', title='Ваши проекты')


@app.route('/profile')
def profile():
    return render_template('profile.html', title='Профиль')


@app.route('/profile/edit')
def edit_profile():
    return render_template('edit_profile.html', title='Редактирование профиля')


@app.route('/matches')
def matches():
    return render_template('matches.html', title='Ваши Эврики!')


if __name__ == '__main__':
    app.run(debug=True)
