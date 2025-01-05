from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, Response as FlaskResponse
from config import Config
from models import db, User, Survey, Response
from forms import (RegistrationForm, LoginForm, SurveyForm, ResponseForm, 
                  ProfileForm, SearchForm)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
import json
import csv
import io

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/')
def indexhp():
    return render_template('indexhomepage.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/404')
def page_not_found():
    return render_template('404.html')

@app.route('/faq')
def faq():
    return render_template('FAQ.html')

@app.route('/offer')
def offer():
    return render_template('offer.html')
  
@app.route('/about')
def offer():
    return render_template('about.html')

# Route principale
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    return render_template('index.html')

# Route admin
@app.route('/admin')
@login_required
def admin():
    if not is_admin():
        flash('Accès non autorisé. Vous devez être administrateur.', 'danger')
        return redirect(url_for('index'))
    surveys = Survey.query.all()
    users = User.query.all()
    return render_template('admin.html', surveys=surveys, users=users)

# Routes d'authentification
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
        user = User.query.filter_by(email=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('index'))
        flash('Email ou mot de passe invalide', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Routes de gestion des sondages
from datetime import datetime

@app.route('/survey/new', methods=['GET', 'POST'])
@login_required
def create_survey():
    form = SurveyForm()
    if form.validate_on_submit():
        try:
            # Récupération des questions du formulaire
            questions_data = form.questions.data if form.questions.data else []

            if not questions_data:
                flash('Veuillez ajouter au moins une question.', 'danger')
                return render_template('survey/create.html', form=form)

            # Validation de la date de fin
            if form.end_date.data <= datetime.now():
                flash('La date de fin doit être ultérieure à la date actuelle.', 'danger')
                return render_template('survey/create.html', form=form)

            # Création du sondage
            survey = Survey(
                title=form.title.data,
                description=form.description.data,
                questions=questions_data,  # Déjà en format JSON
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

    # Si le formulaire n'est pas valide ou méthode GET
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
    
    if survey.author_id != current_user.id and not current_user.role == 'admin':
        flash('Vous n\'êtes pas autorisé à supprimer ce sondage.', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Supprimer d'abord les réponses associées
        Response.query.filter_by(survey_id=survey_id).delete()
        db.session.delete(survey)
        db.session.commit()
        flash('Sondage supprimé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Une erreur est survenue lors de la suppression.', 'danger')
        print(f"Erreur de suppression: {str(e)}")
    
    return redirect(url_for('index'))

# Routes de profil utilisateur
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        if current_user.password == form.current_password.data:
            current_user.email = form.email.data
            if form.new_password.data:
                current_user.password = form.new_password.data
            db.session.commit()
            flash('Profil mis à jour avec succès!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Mot de passe actuel incorrect.', 'danger')
    
    # Pré-remplir l'email
    if request.method == 'GET':
        form.email.data = current_user.email
    
    # Obtenir les statistiques
    surveys_created = Survey.query.filter_by(author_id=current_user.id).count()
    surveys_participated = Response.query.filter_by(user_id=current_user.id).count()
    
    return render_template('user/profile.html', 
                         form=form,
                         surveys_created=surveys_created,
                         surveys_participated=surveys_participated)

# Routes de recherche et filtrage
@app.route('/search')
@login_required
def search_surveys():
    form = SearchForm()
    keyword = request.args.get('keyword', '')
    surveys = Survey.query.filter(Survey.title.contains(keyword)).all()
    return render_template('survey/search.html', surveys=surveys, form=form)

# Routes d'analyse
@app.route('/survey/<int:survey_id>/analytics')
@login_required
def survey_analytics(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    if survey.author_id != current_user.id and current_user.role != 'admin':
        flash('You cannot view these analytics.', 'danger')
        return redirect(url_for('index'))
    responses = Response.query.filter_by(survey_id=survey_id).all()
    # Traitement des données pour l'analyse
    analytics_data = process_analytics(responses)
    return render_template('survey/analytics.html', 
                         survey=survey, 
                         responses=responses,
                         analytics=analytics_data)

def process_analytics(responses):
    # Logique de traitement des données pour l'analyse
    # À implémenter selon vos besoins
    return {}

def is_admin():
    return current_user.is_authenticated and current_user.role == 'admin'

# Ajout des routes pour les dashboards
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.role == 'admin':
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('index'))
    
    # Récupérer tous les sondages avec leurs auteurs
    my_surveys = Survey.query.filter_by(author_id=current_user.id).order_by(Survey.created_at.desc()).all()
    all_surveys = Survey.query.order_by(Survey.created_at.desc()).all()
    users = User.query.all()
    
    return render_template('admin/dashboard2.html',
                         my_surveys=my_surveys,
                         all_surveys=all_surveys,
                         users=users)

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    # Récupérer les sondages de l'utilisateur et les sondages disponibles
    my_surveys = Survey.query.filter_by(author_id=current_user.id).order_by(Survey.created_at.desc()).all()
    available_surveys = Survey.query.filter(
        Survey.is_active == True,
        Survey.end_date > datetime.utcnow(),
        Survey.author_id != current_user.id
    ).order_by(Survey.created_at.desc()).all()
    
    # Récupérer les réponses de l'utilisateur actuel
    my_responses = Response.query.filter_by(user_id=current_user.id).all()

    return render_template('user/dashboard.html',
                         my_surveys=my_surveys,
                         available_surveys=available_surveys,
                         my_responses=my_responses)

# Ajout d'une route pour voir les résultats d'un sondage
@app.route('/survey/<int:survey_id>/results')
@login_required
def view_results(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    if survey.author_id != current_user.id and not current_user.role == 'admin':
        flash('Vous n\'êtes pas autorisé à voir ces résultats.', 'danger')
        return redirect(url_for('index'))
    
    # Get all responses with their respondents
    responses = Response.query.filter_by(survey_id=survey_id)\
        .join(User, Response.user_id == User.id)\
        .add_columns(User.username)\
        .all()
    
    # Aggregate results
    aggregated_results = {}
    individual_responses = []

    for response, username in responses:
        answers = response.get_answers()
        
        # Store individual response data
        individual_responses.append({
            'username': username,
            'submitted_at': response.submitted_at,
            'answers': answers
        })

        # Aggregate answers for statistics
        for question_id, answer in answers.items():
            if question_id not in aggregated_results:
                aggregated_results[question_id] = {}
            
            if isinstance(answer, list):
                for option in answer:
                    aggregated_results[question_id][option] = aggregated_results[question_id].get(option, 0) + 1
            else:
                aggregated_results[question_id][answer] = aggregated_results[question_id].get(answer, 0) + 1

    return render_template('survey/results.html', 
                         survey=survey, 
                         aggregated_results=aggregated_results,
                         individual_responses=individual_responses)


@app.route('/survey/<int:survey_id>')
@login_required
def view_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)

    # Récupérer les réponses associées au sondage
    responses = survey.responses

    # Agrégation des résultats
    results = {}

    for response in responses:
        answers = response.get_answers()  # Récupérer les réponses JSON

        # Parcourir chaque question et réponse
        for question, answer in answers.items():
            # Si la réponse est une liste (choix multiples)
            if isinstance(answer, list):
                for option in answer:
                    if question not in results:
                        results[question] = {}
                    if option not in results[question]:
                        results[question][option] = 0
                    results[question][option] += 1
            else:
                # Gestion des réponses simples
                if question not in results:
                    results[question] = {}
                if answer not in results[question]:
                    results[question][answer] = 0
                results[question][answer] += 1

    return render_template('survey/view.html',
                           survey=survey,
                           results=results)


@app.route('/survey/<int:survey_id>/take', methods=['GET', 'POST'])
@login_required
def take_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    
    # Vérifier si le sondage est actif et non expiré
    if not survey.is_active or survey.is_expired():
        flash('Ce sondage n\'est plus disponible.', 'danger')
        return redirect(url_for('index'))
    
    # Vérifier si l'utilisateur n'a pas déjà répondu
    existing_response = Response.query.filter_by(
        survey_id=survey_id,
        user_id=current_user.id
    ).first()
    
    if existing_response:
        flash('Vous avez déjà répondu à ce sondage.', 'info')
        return redirect(url_for('view_results', survey_id=survey_id))
    
    if request.method == 'POST':
        try:
            answers = {}
            questions = survey.get_questions()
            
            for question in questions:
                q_id = str(question['id'])
                if question['type'] == 'choice':
                    answers[q_id] = request.form.get(f'question_{q_id}')
                elif question['type'] == 'rating':
                    answers[q_id] = int(request.form.get(f'question_{q_id}', 0))
                else:  # text
                    answers[q_id] = request.form.get(f'question_{q_id}', '').strip()
                
                # Vérifier si la réponse est fournie
                if not answers[q_id]:
                    flash('Veuillez répondre à toutes les questions.', 'danger')
                    return render_template('survey/take.html', survey=survey)
            
            # Créer la réponse
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
            print(f"Erreur lors de la soumission du sondage: {str(e)}")
    
    return render_template('survey/take.html', survey=survey)

@app.context_processor
def utility_processor():
    def get_range(start, end):
        return list(range(start, end + 1))
    return dict(get_range=get_range)

@app.route('/survey/<int:survey_id>/export')
@login_required
def export_survey_results(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    if survey.author_id != current_user.id and not current_user.role == 'admin':
        flash('Vous n\'êtes pas autorisé à exporter ces résultats.', 'danger')
        return redirect(url_for('index'))

    # Préparer les données pour l'exportation
    responses = Response.query.filter_by(survey_id=survey_id).all()
    questions = survey.get_questions()

    # Créer une réponse CSV
    def generate_csv():
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Écrire l'en-tête
        header = ['Username', 'Submitted At'] + [q['text'] for q in questions]
        writer.writerow(header)

        # Écrire les données
        for response in responses:
            row = [response.respondent.username, response.submitted_at.strftime('%d/%m/%Y %H:%M')]
            answers = response.get_answers()
            for question in questions:
                answer = answers.get(str(question['id']), '')
                if isinstance(answer, list):
                    answer = ', '.join(answer)
                row.append(answer)
            writer.writerow(row)

        # Retourner le contenu du StringIO
        return output.getvalue()

    csv_data = generate_csv()
    return FlaskResponse(csv_data, mimetype='text/csv', headers={"Content-Disposition": f"attachment;filename=survey_{survey_id}_results.csv"})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
