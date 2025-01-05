from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, SelectField, DateTimeField, EmailField, HiddenField
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
    questions = HiddenField('Questions', validators=[DataRequired()])
    end_date = DateTimeField('Date de fin', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    questions_json = HiddenField('Questions JSON')
    submit = SubmitField('Créer le sondage')

    def validate_questions(form, field):
        print(f"Data reçue pour questions: {field.data}")  # Debug
        if isinstance(field.data, str):
            try:
                questions = json.loads(field.data)
                if not questions_data:
                    raise ValidationError('Au moins une question est requise')
            except json.JSONDecodeError:
                raise ValidationError("Format de questions invalide.")
        elif isinstance(field.data, list):
            questions = field.data
        else:
            raise ValidationError("Format de questions inconnu.")

        if not questions or not isinstance(questions, list):
            raise ValidationError("Veuillez ajouter au moins une question valide.")

        for question in questions:
            if 'text' not in question or 'type' not in question:
                raise ValidationError("Chaque question doit contenir du texte et un type.")


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
