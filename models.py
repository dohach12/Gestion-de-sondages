from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from typing import List, Dict
import json

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    surveys = db.relationship('Survey', backref='author', lazy=True)
    responses = db.relationship('Response', backref='respondent', lazy=True)

class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    questions = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    responses = db.relationship('Response', backref='survey', lazy=True)

    def get_questions(self) -> List[Dict]:
        """Retourne la liste des questions du sondage."""
        # Si self.questions est déjà une liste, retourne-la directement
        if isinstance(self.questions, list):
            return self.questions

        # Si c'est une chaîne JSON, la convertir en liste
        if isinstance(self.questions, str):
            try:
                return json.loads(self.questions)
            except json.JSONDecodeError:
                return []  # En cas d'erreur de décodage, retourne une liste vide

        # Si aucun des deux cas, retourne une liste vide
        return []

    def is_expired(self) -> bool:
        """Vérifie si le sondage est expiré."""
        if not self.end_date:
            return False
        return datetime.utcnow() > self.end_date

    def get_response_count(self) -> int:
        """Retourne le nombre total de réponses."""
        return len(self.responses)

    def get_analytics_data(self) -> Dict:
        """Génère les données d'analyse pour le sondage."""
        responses = self.responses
        questions = self.get_questions()

        analytics = {
            'totalResponses': len(responses),
            'completionRate': self._calculate_completion_rate(),
            'questions': []
        }

        for question in questions:
            question_data = {
                'id': question['id'],
                'type': question['type'],
                'text': question['text'],
                'answers': self._analyze_question_responses(question, responses)
            }
            analytics['questions'].append(question_data)

        return analytics

    def _calculate_completion_rate(self) -> float:
        """Calcule le taux de complétion du sondage."""
        if not self.responses:
            return 0.0

        total_possible = len(self.get_questions())
        completed = sum(1 for response in self.responses
                        if len(response.get_answers()) == total_possible)

        return round((completed / len(self.responses)) * 100, 2)

    def _analyze_question_responses(self, question: Dict, responses: List['Response']) -> List[Dict]:
        """Analyse les réponses pour une question spécifique."""
        analysis_methods = {
            'choice': self._analyze_choice_question,
            'rating': self._analyze_rating_question,
            'text': self._analyze_text_question
        }

        method = analysis_methods.get(question['type'])
        if not method:
            raise ValueError(f"Type de question non supporté: {question['type']}")

        return method(question, responses)

    def _analyze_choice_question(self, question: Dict, responses: List['Response']) -> List[Dict]:
        """Analyse les réponses pour une question à choix."""
        counts = {}
        choices = question.get('choices', [])

        for response in responses:
            answers = response.get_answers()
            answer = answers.get(str(question['id']))
            if answer:
                counts[answer] = counts.get(answer, 0) + 1

        return [{'name': choice, 'count': counts.get(choice, 0)} for choice in choices]

    def _analyze_rating_question(self, question: Dict, responses: List['Response']) -> List[Dict]:
        """Analyse les réponses pour une question avec notation."""
        min_rating = question.get('min_rating', 1)
        max_rating = question.get('max_rating', 5)
        ratings = {i: 0 for i in range(min_rating, max_rating + 1)}

        for response in responses:
            answers = response.get_answers()
            rating = answers.get(str(question['id']))
            if rating and min_rating <= int(rating) <= max_rating:
                ratings[int(rating)] += 1

        return [{'rating': rating, 'count': count}
                for rating, count in sorted(ratings.items())]

    def _analyze_text_question(self, question: Dict, responses: List['Response']) -> List[Dict]:
        """Analyse les réponses pour une question textuelle."""
        text_responses = []
        for response in responses:
            answers = response.get_answers()
            answer = answers.get(str(question['id']))
            if answer:
                text_responses.append({
                    'response': answer,
                    'respondent_id': response.user_id,
                    'submitted_at': response.submitted_at.isoformat()
                })
        return text_responses

    def get_all_responses_detailed(self):
        """Retourne toutes les réponses détaillées pour l'admin"""
        detailed_responses = []
        questions = self.get_questions()

        for response in self.responses:
            answers = response.get_answers()
            response_detail = {
                'user': {
                    'username': response.respondent.username,
                    'email': response.respondent.email
                },
                'submission_date': response.submitted_at,
                'answers': []
            }

            for question in questions:
                answer = {
                    'question': question['text'],
                    'type': question['type'],
                    'answer': answers.get(str(question['id']), 'Non répondu')
                }
                response_detail['answers'].append(answer)

            detailed_responses.append(response_detail)

        return detailed_responses


class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    answers = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_answers(self) -> Dict:
        if isinstance(self.answers, str):
            return json.loads(self.answers)
        return self.answers

    def set_answers(self, answers: Dict) -> None:
        self.answers = json.dumps(answers)
