from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eureka.db'
app.config['SECRET_KEY'] = 'serg'

db = SQLAlchemy(app)
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# Модели для базы данных
# User - таблица пользователей
# Project - таблица проектов
# Matches - таблица совпадений


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nick = db.Column(db.String(16), nullable=False)
    email = db.Column(db.String, nullable=False)
    name = db.Column(db.String)
    second_name = db.Column(db.String)
    about = db.Column(db.Text)
    level = db.Column(db.String, nullable=False)
    main_language = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

    def __repr__(self):
        return self.nick

    def is_authenticated(self):
        return True


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    about = db.Column(db.Text, nullable=False)
    image = db.Column(db.String)
    front_language = db.Column(db.Integer, nullable=False)
    back_language = db.Column(db.String, nullable=False)
    level = db.Column(db.String, nullable=False)
    founder_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return self.title


class Matches(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    project_id = db.Column(db.Integer, nullable=False)
    is_approved = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'{self.user_id} user + {self.project_id} = {self.is_approved}'


# Функции отслеживания страниц


@app.route('/')
def main():
    return render_template('main.html', title='Главная страница')


@app.route('/projects')
@login_required
def projects():
    projects = db.session.query(Project).filter_by(founder_id=current_user.id).all()
    return render_template('projects.html', title='Ваши проекты')


@app.route('/projects/create', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        title = request.form['title']
        img = request.form['img']
        about = request.form['about']
        front_language = int(request.form['front_language'])
        back_language = request.form['back_language']
        level = request.form['level']
        founder_id = int(current_user.id)

        project = Project(title=title, image=img, about=about, front_language=front_language,
                          back_language=back_language, founder_id=founder_id, level=level)

        try:
            db.session.add(project)
            db.session.commit()
            return redirect('/projects')
        except Exception as e:
            return render_template('error.html', title='Ошибка', error=e)
    return render_template('create_project.html', title='Создание проекта')


@app.route('/profile/<int:user_id>')
def profile(user_id):
    return render_template('profile.html', title='Профиль', user=User.query.get(user_id))


@app.route('/profile')
@login_required
def profile_owner():
    return render_template('profile_owner.html', title='Профиль', user=current_user)


@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = current_user
    if request.method == 'POST':
        user.email = request.form['email']
        if request.form['name']:
            user.name = request.form['name']
        if request.form['second_name']:
            user.second_name = request.form['second_name']
        if request.form['about']:
            user.about = request.form['about']
        user.main_language = request.form['main_language']
        user.level = request.form['level']

        try:
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)
            return redirect('/profile')
        except Exception as e:
            return render_template('error.html', title='Ошибка', error=e)
    return render_template('edit_profile.html', title='Редактирование профиля', user=current_user)


@app.route('/matches')
def matches():
    return render_template('matches.html', title='Ваши Эврики!')


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':

        nick = request.form['nick']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        main_language = request.form['main_language']
        level = request.form['level']

        if not db.session.query(User).filter_by(nick=nick).first() and not db.session.query(User).filter_by(
                email=email).first():

            user = User(nick=nick, email=email, password=password, main_language=main_language,
                        level=level)

            try:
                db.session.add(user)
                db.session.commit()
                flash('Регистрация прошла успешно!', 'success')
                return redirect('/login')
            except Exception as e:
                return render_template('error.html', title='Ошибка', error=e)
        else:
            return render_template('error.html', title='Ошибка', error='Already registered')
    return render_template('registration.html', title='Регистрация')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect('/profile')
    if request.method == 'POST':
        user = User.query.filter_by(nick=request.form['nick']).first()
        if user:
            if check_password_hash(user.password, request.form['password']):
                login_user(user)
                print(user)
                return redirect('/profile')
        return redirect('/login')
    return render_template('login.html', title='Авторизация')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.errorhandler(401)
def custom_401(error):
    return redirect('/login')


@app.errorhandler(404)
def custom_404(error):
    return render_template('404.html', title='Хмммм...')


if __name__ == '__main__':
    app.run(debug=True)
