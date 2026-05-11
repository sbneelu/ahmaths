"""
Tests for security fixes: open-redirect prevention, POST-only logout,
POST-only delete_progress, and email-enumeration protection on password reset.
"""


def test_login_blocks_open_redirect(client, app):
    """Login with an external `next` URL must redirect to /home, not the attacker site."""
    from ahmaths import db, bcrypt
    from ahmaths.models import User

    with app.app_context():
        hashed = bcrypt.generate_password_hash('testpassword')
        if isinstance(hashed, bytes):
            hashed = hashed.decode('utf-8')
        db.session.add(User(email='redirect@example.com', password=hashed))
        db.session.commit()

    response = client.post(
        '/login?next=https://evil.com/',
        data={'email': 'redirect@example.com', 'password': 'testpassword'},
        follow_redirects=False,
    )
    assert response.status_code == 302
    location = response.headers['Location']
    assert 'evil.com' not in location
    assert location.endswith('/home') or location == '/home'


def test_login_allows_safe_relative_next(client, app):
    """Login with a safe relative `next` must redirect to that path."""
    from ahmaths import db, bcrypt
    from ahmaths.models import User

    with app.app_context():
        hashed = bcrypt.generate_password_hash('testpassword')
        if isinstance(hashed, bytes):
            hashed = hashed.decode('utf-8')
        db.session.add(User(email='safenext@example.com', password=hashed))
        db.session.commit()

    response = client.post(
        '/login?next=/account',
        data={'email': 'safenext@example.com', 'password': 'testpassword'},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/account')


def test_logout_get_not_allowed(client):
    """Unauthenticated GET to /logout must return 405 (method not allowed)."""
    response = client.get('/logout')
    assert response.status_code == 405


def test_logout_post_logs_out(auth_client):
    """Authenticated POST to /logout must redirect and end the session."""
    response = auth_client.post('/logout', follow_redirects=False)
    assert response.status_code == 302
    # After logout, accessing /account must redirect to login.
    response = auth_client.get('/account', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_delete_progress_get_not_allowed(auth_client):
    """Authenticated GET to /account/delete_progress/all must return 405."""
    response = auth_client.get('/account/delete_progress/all')
    assert response.status_code == 405


def test_request_reset_no_account_does_not_reveal(client):
    """Password reset for non-existent email must not reveal that fact."""
    response = client.post(
        '/reset_password',
        data={'email': 'noone@example.com'},
        follow_redirects=False,
    )
    assert response.status_code == 302
    # Follow redirect and check flashed content does not leak account existence.
    followed = client.get(response.headers['Location'])
    body = followed.data.lower()
    assert b'no account' not in body
    assert b"doesn't exist" not in body
    assert b'does not exist' not in body
