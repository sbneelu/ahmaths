"""
Tests for database models.
"""
import pytest
from ahmaths.models import User, Topic, Subtopic, Question, Paper
from ahmaths import db, bcrypt


def test_user_model(app):
    """Test User model creation."""
    with app.app_context():
        hashed_password = bcrypt.generate_password_hash('password')
        # Handle both bytes and str return types for compatibility
        if isinstance(hashed_password, bytes):
            hashed_password = hashed_password.decode('utf-8')
        user = User(
            email='test@example.com',
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()

        retrieved = User.query.filter_by(email='test@example.com').first()
        assert retrieved is not None
        assert retrieved.email == 'test@example.com'
        assert bcrypt.check_password_hash(retrieved.password, 'password')


def test_user_reset_token(app):
    """Test password reset token generation and verification."""
    with app.app_context():
        hashed_password = bcrypt.generate_password_hash('password')
        # Handle both bytes and str return types for compatibility
        if isinstance(hashed_password, bytes):
            hashed_password = hashed_password.decode('utf-8')
        user = User(
            email='test@example.com',
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()

        # Generate token
        token = user.get_reset_token()
        assert token is not None
        assert isinstance(token, str)

        # Verify token with default max_age (1800 seconds)
        verified_user = User.verify_reset_token(token, max_age=1800)
        assert verified_user is not None
        assert verified_user.id == user.id
        assert verified_user.email == user.email


def test_user_reset_token_expired(app):
    """Test that expired tokens are rejected."""
    with app.app_context():
        hashed_password = bcrypt.generate_password_hash('password')
        # Handle both bytes and str return types for compatibility
        if isinstance(hashed_password, bytes):
            hashed_password = hashed_password.decode('utf-8')
        user = User(
            email='test@example.com',
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()

        # Generate token
        token = user.get_reset_token()

        # Wait a moment and verify with very short max_age
        import time
        time.sleep(1)  # Wait a full second
        # Verify with max_age of 0.5 seconds - token should be expired
        verified_user = User.verify_reset_token(token, max_age=0.5)
        assert verified_user is None


def test_user_reset_token_invalid(app):
    """Test that invalid tokens are rejected."""
    with app.app_context():
        verified_user = User.verify_reset_token('invalid-token', max_age=1800)
        assert verified_user is None


def test_topic_model(app):
    """Test Topic model."""
    with app.app_context():
        topic = Topic(topic_id='integration', topic_name='Integration')
        db.session.add(topic)
        db.session.commit()

        retrieved = Topic.query.filter_by(topic_id='integration').first()
        assert retrieved is not None
        assert retrieved.topic_name == 'Integration'


def test_subtopic_model(app):
    """Test Subtopic model with relationship."""
    with app.app_context():
        topic = Topic(topic_id='integration', topic_name='Integration')
        db.session.add(topic)
        db.session.commit()

        subtopic = Subtopic(
            subtopic_id='substitution',
            subtopic_name='Integration by Substitution',
            topic_id='integration'
        )
        db.session.add(subtopic)
        db.session.commit()

        retrieved = Subtopic.query.filter_by(subtopic_id='substitution').first()
        assert retrieved is not None
        assert retrieved.subtopic_name == 'Integration by Substitution'
        assert retrieved.topic.topic_name == 'Integration'


def test_question_model(app):
    """Test Question model."""
    with app.app_context():
        question = Question(
            question_id='2020_p1_q1',
            paper='2020_p1',
            question_number='1',
            marks=5,
            topics='integration',
            subtopics='substitution'
        )
        db.session.add(question)
        db.session.commit()

        retrieved = Question.query.filter_by(question_id='2020_p1_q1').first()
        assert retrieved is not None
        assert retrieved.marks == 5
        assert retrieved.paper == '2020_p1'


def test_paper_model(app):
    """Test Paper model."""
    with app.app_context():
        paper = Paper(paper_id='2020_p1', paper_name='2020 Paper 1')
        db.session.add(paper)
        db.session.commit()

        retrieved = Paper.query.filter_by(paper_id='2020_p1').first()
        assert retrieved is not None
        assert retrieved.paper_name == '2020 Paper 1'
