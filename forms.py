from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, SelectField, DateTimeField, EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo
import json
from wtforms.validators import ValidationError

class RegistrationForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', 
                         validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                       validators=[DataRequired(), Email()])
    role = SelectField('Type de compte',
                      choices=[
                          ('user', 'Participant'),
                          ('admin', 'Administrateur')
                      ],
                      validators=[DataRequired()])
    password = PasswordField('Mot de passe', 
                           validators=[DataRequired()])
    confirm_password = PasswordField('Confirmer le mot de passe',
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('S\'inscrire')

class LoginForm(FlaskForm):
    username = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Connexion')

class SurveyForm(FlaskForm):
    title = StringField('Titre du sondage', validators=[DataRequired()])
    description = TextAreaField('Description')
    questions = TextAreaField('Questions (format JSON)', validators=[DataRequired()])
    end_date = DateTimeField('Date de fin', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    submit = SubmitField('Créer le sondage')

    def validate_questions(self, field):
        try:
            questions = json.loads(field.data)
            if not isinstance(questions, list):
                raise ValidationError("Les questions doivent être une liste JSON.")
            for question in questions:
                if 'text' not in question or 'type' not in question:
                    raise ValidationError("Chaque question doit avoir un champ 'text' et 'type'.")
        except json.JSONDecodeError:
            raise ValidationError("Format JSON invalide. Veuillez corriger les erreurs de syntaxe.")

class ResponseForm(FlaskForm):
    answers = TextAreaField('Your Answers', validators=[DataRequired()])
    submit = SubmitField('Submit Response')

class ProfileForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    current_password = PasswordField('Mot de passe actuel', validators=[DataRequired()])
    new_password = PasswordField('Nouveau mot de passe')
    confirm_new_password = PasswordField('Confirmer le nouveau mot de passe', 
                                       validators=[EqualTo('new_password')])
    submit = SubmitField('Mettre à jour')

class SearchForm(FlaskForm):
    keyword = StringField('Search Keyword')
    submit = SubmitField('Search')