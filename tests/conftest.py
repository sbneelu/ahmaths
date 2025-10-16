"""
Pytest configuration and fixtures for testing.
"""
import pytest
import os
import tempfile

# Set test configuration BEFORE importing ahmaths
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'
os.environ['DATABASE_URL'] = 'sqlite:///test.db'
os.environ['TESTING'] = 'True'
os.environ['WTF_CSRF_ENABLED'] = 'False'

from ahmaths import create_app, db
from ahmaths.models import User, Topic, Subtopic, Question, Paper


@pytest.fixture(scope='function')
def app():
    """Create and configure a test app instance."""
    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp()

    # Create app with test database
    from ahmaths.config import Config

    class TestConfig(Config):
        TESTING = True
        WTF_CSRF_ENABLED = False
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        SECRET_KEY = 'test-secret-key-for-testing-only'

    app = create_app(TestConfig)

    # Create tables
    with app.app_context():
        db.create_all()

        # Add basic test data (only if needed)
        existing_topic = Topic.query.filter_by(topic_id='test_topic').first()
        if not existing_topic:
            topic = Topic(topic_id='test_topic', topic_name='Test Topic')
            db.session.add(topic)
            db.session.commit()

    yield app

    # Cleanup
    with app.app_context():
        db.session.remove()
        db.drop_all()
    try:
        os.close(db_fd)
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def auth_client(client, app):
    """Create an authenticated test client."""
    with app.app_context():
        from ahmaths import bcrypt
        # Create a test user
        hashed_password = bcrypt.generate_password_hash('testpassword')
        # Handle both bytes and str return types for compatibility
        if isinstance(hashed_password, bytes):
            hashed_password = hashed_password.decode('utf-8')
        user = User(email='test@example.com', password=hashed_password)
        db.session.add(user)
        db.session.commit()

    # Login
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    })

    return client
