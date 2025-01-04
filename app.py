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
        if user and user.password == form.password.data:
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
                questions=questions_data,
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

    return render_template('survey/create.html', form=form)

@app.route('/survey/<int:survey_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)

    if not is_admin() and survey.author_id != current_user.id:
        flash("Vous n'êtes pas autorisé à modifier ce sondage.", 'danger')
        return redirect(url_for('index'))

    form = SurveyForm(obj=survey)

    if form.validate_on_submit():
        try:
            questions = []
            question_texts = request.form.getlist('question_text[]')
            question_types = request.form.getlist('question_type[]')
            question_choices = request.form.getlist('question_choices[]')
            question_ids = request.form.getlist('question_id[]')

            for i in range(len(question_texts)):
                question = {
                    "id": question_ids[i] if question_ids[i] else str(i),
                    "text": question_texts[i],
                    "type": question_types[i],
                }
                if question_types[i] == 'choice':
                    question["choices"] = [choice.strip() for choice in question_choices[i].split(',') if choice]

                questions.append(question)

            survey.title = form.title.data
            survey.description = form.description.data
            survey.questions = json.dumps(questions)
            survey.end_date = form.end_date.data

            db.session.commit()
            flash('Sondage mis à jour avec succès!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification : {str(e)}', 'danger')

    return render_template('survey/edit.html', form=form, survey=survey)

@app.route('/survey/<int:survey_id>/delete')
@login_required
def delete_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    
    if survey.author_id != current_user.id and not is_admin():
        flash('Vous n\'êtes pas autorisé à supprimer ce sondage.', 'danger')
        return redirect(url_for('index'))
    
    try:
        Response.query.filter_by(survey_id=survey_id).delete()
        db.session.delete(survey)
        db.session.commit()
        flash('Sondage supprimé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Une erreur est survenue lors de la suppression.', 'danger')
        print(f"Erreur de suppression: {str(e)}")
    
    return redirect(url_for('index'))

@app.route('/survey/<int:survey_id>/take', methods=['GET', 'POST'])
@login_required
def take_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    
    if not survey.is_active or survey.end_date <= datetime.now():
        flash('Ce sondage n\'est plus disponible.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            answers = {}
            for question in survey.get_questions():
                q_id = str(question['id'])
                answers[q_id] = request.form.get(f'question_{q_id}', '')
                if not answers[q_id]:
                    flash('Veuillez répondre à toutes les questions.', 'danger')
                    return render_template('survey/take.html', survey=survey)

            response = Response(
                survey_id=survey_id,
                user_id=current_user.id,
                answers=json.dumps(answers)
            )

            db.session.add(response)
            db.session.commit()
            
            flash('Merci pour votre participation!', 'success')
            return redirect(url_for('view_results', survey_id=survey_id))
        except Exception as e:
            db.session.rollback()
            flash('Une erreur est survenue. Veuillez réessayer.', 'danger')

    return render_template('survey/take.html', survey=survey)

@app.route('/admin/survey/<int:survey_id>/results')
@login_required
def admin_survey_results(survey_id):
    if not is_admin():
        flash("Accès non autorisé.", "danger")
        return redirect(url_for('index'))

    survey = Survey.query.get_or_404(survey_id)
    responses = [
        {
            'user': response.respondent,
            'submission_date': response.submitted_at,
            'answers': [
                {
                    'question': question['text'],
                    'type': question['type'],
                    'answer': response.get_answers().get(str(question['id']), "Non répondu")
                }
                for question in survey.get_questions()
            ]
        }
        for response in survey.responses
    ]
    return render_template('admin/survey_results.html', survey=survey, responses=responses)

@app.route('/survey/<int:survey_id>/results')
@login_required
def view_results(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    if not is_admin() and survey.author_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à voir ces résultats.', 'danger')
        return redirect(url_for('index'))

    responses = Response.query.filter_by(survey_id=survey_id).all()
    return render_template('survey/results.html', survey=survey, responses=responses)

@app.route('/survey/<int:survey_id>/results_graph')
@login_required
def view_results_graph(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    if not is_admin() and survey.author_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à voir ces résultats.', 'danger')
        return redirect(url_for('index'))

    responses = Response.query.filter_by(survey_id=survey_id).all()

    # Préparation des données pour les graphiques
    questions = json.loads(survey.questions)
    results = {q['text']: {} for q in questions}

    for response in responses:
        answers = json.loads(response.answers)
        for question in questions:
            q_id = str(question['id'])
            q_text = question['text']
            answer = answers.get(q_id, None)
            if not answer:
                continue
            if isinstance(answer, list):  # Gestion des choix multiples
                for option in answer:
                    results[q_text][option] = results[q_text].get(option, 0) + 1
            else:
                results[q_text][answer] = results[q_text].get(answer, 0) + 1

    return render_template('survey/results_graph.html', survey=survey, results=results)


@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))

    my_surveys = Survey.query.filter_by(author_id=current_user.id).order_by(Survey.created_at.desc()).all()
    available_surveys = Survey.query.filter(
        Survey.is_active == True,
        Survey.end_date > datetime.utcnow(),
        Survey.author_id != current_user.id
    ).order_by(Survey.created_at.desc()).all()

    return render_template('user/dashboard.html', 
                           my_surveys=my_surveys, 
                           available_surveys=available_surveys)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not is_admin():
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('index'))

    my_surveys = Survey.query.filter_by(author_id=current_user.id).order_by(Survey.created_at.desc()).all()
    all_surveys = Survey.query.order_by(Survey.created_at.desc()).all()
    users = User.query.all()

    return render_template('admin/dashboard.html',
                           my_surveys=my_surveys,
                           all_surveys=all_surveys,
                           users=users)

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