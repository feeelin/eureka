from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eureka.db'
app.config['SECRET_KEY'] = 'serg'

db = SQLAlchemy(app)
login_manager = LoginManager(app)

# массив languages нужен для заполнения данных в некоторых формах, например, в registry

languages = ['Python', 'Java', 'C', 'C++', 'C#', 'JavaScript', 'PHP',
             'GO', 'Assembly', 'Swift', 'Kotlin', 'Ruby', 'Rust']


# load_user подгружает в сессию информацию о залогиненом пользователе


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# класс User является моделью для таблицы User в базе данных проекта и описывает форматы данных
# метод is_authenticated помогает функции load_user ориентироваться в состояниях пользователя


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
    img = db.Column(db.String)

    def __repr__(self):
        return self.nick

    def is_authenticated(self):
        return True


# класс Project является моделью для таблицы Project в базе данных проекта и описывает форматы данных


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    about = db.Column(db.Text, nullable=False)
    image = db.Column(db.String)
    front_language = db.Column(db.Integer, nullable=False)
    back_language = db.Column(db.String, nullable=False)
    level = db.Column(db.String, nullable=False)
    founder_id = db.Column(db.Integer, nullable=False)
    intro = db.Column(db.String(240))

    def __repr__(self):
        return self.title


# класс Matches является моделью для таблицы Matches в базе данных проекта и описывает форматы данных,
# является связующей между двумя другими моделями


class Matches(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    project_id = db.Column(db.Integer, nullable=False)
    is_approved = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'{self.user_id} user + {self.project_id} = {self.is_approved}'

    # класс Achievements является моделью БД для хранения данных о статусах пользователя


class Achievements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    coffee = db.Column(db.Integer)
    production_lost = db.Column(db.Integer)
    teamlead_shouts = db.Column(db.Integer)

    def __repr__(self):
        return f'{self.id}'


# функция main отслеживает url '/' и при запросе возвращает HTML-страницу, подставляя в блок title название


@app.route('/')
def main():
    return render_template('main.html', title='Главная страница')


# Функция search отслеживает url '/search' и при запросе формирует все подходящие для пользователя проекты, подставляя
# их в HTML-документ. Работает только для авторизованных пользователей


@app.route('/search')
@login_required
def search():
    projects = db.session.query(Project).filter_by(back_language=current_user.main_language).all()
    id = [i.founder_id for i in projects]

    founders = []
    for i in id:
        founders.append(db.session.query(User).filter_by(id=i).first())

    return render_template('search.html', title='Поиск', projects=projects, founders=founders)


# функция projects отслеживает url '/projects' и при запросе формирует все проекты пользователя, подставляя
# их в HTML-документ


@app.route('/projects')
@login_required
def projects():
    projects = db.session.query(Project).filter_by(founder_id=current_user.id).all()
    return render_template('projects.html', title='Ваши проекты', projects=projects)


# функция project_profile достаёт из БД данные о проекте по его id и формирует HTML-документ с этими данными
# также достаёт данные о том, оставлял ли пользователь отзыв на этот проект


@app.route('/projects/<int:id>')
def project_profile(id):
    project = db.session.query(Project).filter_by(id=id).first()
    like = db.session.query(Matches).filter_by(user_id=current_user.id, project_id=id).first()
    return render_template('project_profile.html', title=project.title, project=project, user=current_user, like=like)


# функция project_edit достаёт из БД данные о проекте по его id и формирует форму для обновления данных


@app.route('/projects/<int:id>/edit', methods=['POST', 'GET'])
def project_edit(id):
    project = db.session.query(Project).filter_by(id=id).first()
    if project.founder_id == current_user.id:
        if request.method == 'POST':
            project.title = request.form['title']
            if request.form['about']:
                project.about = request.form['about']
            if request.form['img']:
                project.image = request.form['img']
            if request.form['intro']:
                project.intro = request.form['intro']
            project.front_language = request.form['front_language']
            project.back_language = request.form['back_language']
            project.level = request.form['level']

            try:
                db.session.add(project)
                db.session.commit()
                db.session.refresh(project)
                return redirect(f'/projects/{project.id}')
            except Exception as e:
                return render_template('error.html', title='Ошибка', error='Не удалось обновить проект')
        return render_template('edit_project.html', title=project.title, project=project, languages=languages)
    return redirect('/')


# функция create_project создаёт форму для объявления нового объекта в БД и в случае корректного заполнения сохраняет
# её данные в таблицу Projects


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
        intro = request.form['intro']
        founder_id = int(current_user.id)

        project = Project(title=title, image=img, about=about, front_language=front_language,
                          back_language=back_language, founder_id=founder_id, level=level, intro=intro)

        try:
            db.session.add(project)
            db.session.commit()
            return redirect('/projects')
        except Exception as e:
            return render_template('error.html', title='Ошибка', error='Не удалось создать проект')
    return render_template('create_project.html', title='Создание проекта', languages=languages)


# Функция delete_project берёт данные об объекте в БД и запускает процесс его удаления. Доступна только автору
# удаляемого проекта


@app.route('/projects/<int:project_id>/delete')
@login_required
def delete_project(project_id):
    project = project = db.session.query(Project).filter_by(id=project_id).first()
    if current_user.id == project.founder_id:
        try:
            db.session.delete(project)
            db.session.commit()
            return redirect('/projects')
        except:
            return render_template('error.html', title='Ошибка', error='Удаление проекта не удалось')
    return redirect('/')


# функция profile выводит профиль пользователя по его уникальному идентификатору


@app.route('/profile/<int:user_id>')
def profile(user_id):
    stats = db.session.query(Achievements).filter_by(user_id=user_id).first()
    return render_template('profile.html', title='Профиль', user=User.query.get(user_id), stats=stats)


# функция profile_owner открывает профиль пользователя для самого пользователя с возможностью выхода из аккаунта и
# редактирования данных


@app.route('/profile')
@login_required
def profile_owner():
    stats = db.session.query(Achievements).filter_by(user_id=current_user.id).first()
    return render_template('profile_owner.html', title='Профиль', user=current_user, stats=stats)


# функция profile edit загружает форму для редактирования данных профиля пользователя


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
        if request.form['img']:
            user.img = request.form['img']
        user.main_language = request.form['main_language']
        user.level = request.form['level']

        try:
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)
            return redirect('/profile')
        except Exception as e:
            return render_template('error.html', title='Ошибка', error=e)
    return render_template('edit_profile.html', title='Редактирование профиля', user=current_user, languages=languages)


# функция сверяет отклики пользователя и ответы проджект-файндера, обновляя страницу с Эвриками!


@app.route('/matches')
@login_required
def matches():
    projects = db.session.query(Project).filter_by(founder_id=current_user.id).all()
    matched_users = []

    for proj in projects:
        for j in db.session.query(Matches).filter_by(project_id=proj.id).all():
            matched_users.append((j.user_id, j.project_id))

    people = []
    for match in matched_users:
        people.append([db.session.query(User).filter_by(id=match[0]).first(),
                       db.session.query(Project).filter_by(id=match[1]).first()])

    matches = db.session.query(Matches).filter_by(user_id=current_user.id, is_approved=1).all()
    print(matches)
    projects = []
    emails = []

    for i in matches:
        project = db.session.query(Project).filter_by(id=i.project_id).first()
        user = db.session.query(User).filter_by(id=project.founder_id).first()
        projects.append(project.title)
        emails.append(user.email)

    return render_template('matches.html', title='Эврики!', user=people, projects=projects, emails=emails)


# функция like занимается отправлением отзыва в базу данных, после чего возвращает пользователя обратно на страницу
# проекта


@app.route('/projects/<int:project_id>/like/<int:user_id>')
def like(project_id, user_id):
    match = Matches(user_id=user_id, project_id=project_id)
    try:
        db.session.add(match)
        db.session.commit()
        return redirect(f'/projects/{project_id}')
    except:
        return render_template('error.html', title='Ошибка', error='Не удалось отправить отклик')


# метод delete_match удаляет из БД запрос пользователя на участие в проекте, если проджект-фаундер не примет его
# заявку


@app.route('/matches/<int:user_id>/<int:project_id>/delete')
def delete_match(user_id, project_id):
    match = db.session.query(Matches).filter_by(user_id=user_id, project_id=project_id).first()
    try:
        db.session.delete(match)
        db.session.commit()
        return redirect('/matches')
    except:
        return render_template('error.html', title='Ошибка', error='Не удалось удалить')


# функция approve_login прямо противоположна предыдущей и наоборот занимается подтверждением заявки со стороны
# фаундера


@app.route('/matches/<int:user_id>/<int:project_id>/eureka')
@login_required
def approve_login(user_id, project_id):
    project = db.session.query(Project).filter_by(founder_id=current_user.id).first()
    if project.founder_id == current_user.id:
        match = db.session.query(Matches).filter_by(user_id=user_id, project_id=project_id).first()
        try:
            match.is_approved = 1
            db.session.add(match)
            db.session.commit()
            return redirect('/matches')
        except:
            return render_template('error.html', title='Ошибка', error='Не удалось подтвердить Эврику')


# форма для регистрации пользователя и занесения данных в таблицу User ДБ


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
                return redirect('/login')
            except Exception as e:
                return render_template('error.html', title='Ошибка', error=e)
        else:
            return render_template('error.html', title='Ошибка',
                                   error='Пользователь с такими данными уже зарегистрирован')
    return render_template('registration.html', title='Регистрация', languages=languages)


# login осуществляет авторизацию пользователя на сайте


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect('/profile')
    if request.method == 'POST':
        user = User.query.filter_by(nick=request.form['nick']).first()
        if user:
            if check_password_hash(user.password, request.form['password']):
                login_user(user)
                return redirect('/profile')
        else:
            user = User.query.filter_by(email=request.form['nick']).first()
            if user:
                if check_password_hash(user.password, request.form['password']):
                    login_user(user)
                    return redirect('/profile')
        return render_template('error.html', title='Ошибка', error='Введённые данные недействительны')
    return render_template('login.html', title='Авторизация')


# функция logout используется для переадресации из профиля пользователя и дальнейшей деаутентификации


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


# два метода необходимы для более комфортного отображения ошибок на сайте
# конкретнее для ошибок 401 и 404


@app.errorhandler(401)
def custom_401(error):
    return redirect('/login')


@app.errorhandler(404)
def custom_404(error):
    return render_template('404.html', title='Хмммм...')


# метод stats предназначен для формирования шутливой статистики


@app.route('/profile/stats', methods=['POST', 'GET'])
def stats():
    stats = db.session.query(Achievements).filter_by(user_id=current_user.id).first()
    print(stats)

    if request.method == 'POST':

        if stats:
            stats.coffee = request.form['coffee']
            stats.production_lost = request.form['production_lost']
            stats.teamlead_shouts = request.form['teamlead_shouts']

        else:
            coffee = request.form['coffee']
            production_lost = request.form['production_lost']
            teamlead_shouts = request.form['teamlead_shouts']
            stat = Achievements(user_id=current_user.id, coffee=coffee, production_lost=production_lost,
                                 teamlead_shouts=teamlead_shouts)

        try:
            db.session.add(stats)
            db.session.commit()
            return redirect('/profile')
        except Exception as e:
            print(e)
            return render_template('error.html', title='Ошибка', error='Не удалось обновить статистику')

    return render_template('make_stats.html', title='Добавление статистики', stats=stats)


if __name__ == '__main__':
    app.run(debug=True)
