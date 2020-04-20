from flask import current_app
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature
from ahmaths import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    progress = db.Column(db.Text, nullable=False, default='partial_fractions:0,binomial_theorem:0,differentiation:0,integration:0,differential_equations:0,functions_graphs:0,systems_of_equations:0,complex_numbers:0,sequences_series:0,maclaurin_series:0,matrices:0,vectors:0,methods_of_proof:0,number_theory:0')
    partial_fractions = db.Column(db.Text, nullable=False, default='')
    binomial_theorem = db.Column(db.Text, nullable=False, default='')
    differentiation = db.Column(db.Text, nullable=False, default='')
    integration = db.Column(db.Text, nullable=False, default='')
    differential_equations = db.Column(db.Text, nullable=False, default='')
    functions_graphs = db.Column(db.Text, nullable=False, default='')
    systems_of_equations = db.Column(db.Text, nullable=False, default='')
    complex_numbers = db.Column(db.Text, nullable=False, default='')
    sequences_series = db.Column(db.Text, nullable=False, default='')
    maclaurin_series = db.Column(db.Text, nullable=False, default='')
    matrices = db.Column(db.Text, nullable=False, default='')
    vectors = db.Column(db.Text, nullable=False, default='')
    methods_of_proof = db.Column(db.Text, nullable=False, default='')
    number_theory = db.Column(db.Text, nullable=False, default='')

    def get_reset_token(self, expires_seconds=1800):
        s = Serializer(current_app.config['SECRET_KEY'], expires_seconds)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except BadSignature:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.email}')"


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.String(32), unique=True, nullable=False)
    topic_name = db.Column(db.String(120), unique=True, nullable=False)
    subtopics = db.relationship('Subtopic', backref='topic', lazy=True)

    def __repr__(self):
        return f"Topic('{self.topic_id}', '{self.topic_name}')"


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.String(32), unique=True, nullable=False)
    paper = db.Column(db.String(32))
    question_number = db.Column(db.String(32), nullable=False)
    marks = db.Column(db.Integer, nullable=False)
    video = db.Column(db.String(30))
    topics = db.Column(db.Text, nullable=False, default='')
    subtopics = db.Column(db.Text, nullable=False, default='')

    def __repr__(self):
        return f"Question('{self.question_id}', '{self.marks}', {self.video})"


class Subtopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subtopic_id = db.Column(db.String(32), unique=True, nullable=False)
    subtopic_name = db.Column(db.String(120), unique=True, nullable=False)
    topic_id = db.Column(db.String(32), db.ForeignKey('topic.topic_id'), nullable=False)

    def __repr__(self):
        return f"Subtopic('{self.subtopic_id}', '{self.subtopic_name}', '{self.topic_id}')"


class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paper_id = db.Column(db.String(50))
    paper_name = db.Column(db.String(100))

    def __repr__(self):
        return f"Paper('{self.paper_id}', '{self.paper_name}')"
