from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from config import Config
from models import db, User, Survey, Response
from forms import (RegistrationForm, LoginForm, SurveyForm, ResponseForm, 
                  ProfileForm, SearchForm)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
import json

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    return render_template('index.html')

@app.route('/admin')
@login_required
def admin():
    if not is_admin():
        flash('Accès non autorisé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('index'))
    surveys = Survey.query.all()
    users = User.query.all()
    return render_template('admin.html', surveys=surveys, users=users)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Un compte existe déjà avec cet email.', 'danger')
                return render_template('register.html', form=form)

            user = User(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data
            )
            user.password = form.password.data
            
            db.session.add(user)
            db.session.commit()
            
            flash(f'Compte créé avec succès! Bienvenue {user.username}!', 'success')
            login_user(user)
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('Une erreur est survenue lors de l\'inscription.', 'danger')
            print(f"Erreur d'inscription: {str(e)}")
            
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        flash('Email ou mot de passe invalide', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/survey/new', methods=['GET', 'POST'])
@login_required
def create_survey():
    form = SurveyForm()
    if form.validate_on_submit():
        try:
            questions_data = form.questions.data if form.questions.data else []

            if not questions_data:
                flash('Veuillez ajouter au moins une question.', 'danger')
                return render_template('survey/create.html', form=form)

            if form.end_date.data <= datetime.now():
                flash('La date de fin doit être ultérieure à la date actuelle.', 'danger')
                return render_template('survey/create.html', form=form)

            survey = Survey(
                title=form.title.data,
                description=form.description.data,
                questions=json.dumps(questions_data),
                end_date=form.end_date.data,
                author_id=current_user.id,
                is_active=True
            )

            db.session.add(survey)
            db.session.commit()

            flash('Sondage créé avec succès!', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            flash(f'Une erreur est survenue: {str(e)}', 'danger')
            
    return render_template('survey/create.html', form=form)

@app.route('/survey/<int:survey_id>/results')
@login_required
def view_results(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    if not is_admin() and survey.author_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à voir ces résultats.', 'danger')
        return redirect(url_for('index'))
    
    responses = Response.query.filter_by(survey_id=survey_id).all()
    return render_template('survey/results.html', survey=survey, responses=responses)

@app.route('/survey/<int:survey_id>')
@login_required
def view_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    results = {}
    
    for response in survey.responses:
        answers = response.get_answers()
        for question, answer in answers.items():
            if question not in results:
                results[question] = {}
                
            if isinstance(answer, list):
                for option in answer:
                    results[question][option] = results[question].get(option, 0) + 1
            else:
                results[question][answer] = results[question].get(answer, 0) + 1

    return render_template('survey/view.html', survey=survey, results=results)

def is_admin():
    return current_user.is_authenticated and current_user.role == 'admin'

@app.context_processor
def utility_processor():
    def get_range(start, end):
        return list(range(start, end + 1))
    return dict(get_range=get_range)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)