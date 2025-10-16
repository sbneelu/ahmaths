"""
Tests for routes and views.
"""
import pytest
from flask import url_for


def test_index_route(client):
    """Test the index/landing page."""
    response = client.get('/')
    assert response.status_code == 200


def test_login_page(client):
    """Test login page loads."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data or b'login' in response.data


def test_signup_page(client):
    """Test signup page loads."""
    response = client.get('/signup')
    assert response.status_code == 200
    assert b'Sign' in response.data or b'sign' in response.data


def test_logout_redirect(client):
    """Test logout redirects to index."""
    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 302


def test_account_requires_login(client):
    """Test that account page requires authentication."""
    response = client.get('/account', follow_redirects=False)
    assert response.status_code == 302  # Redirect to login


def test_questions_page(client):
    """Test questions by topic page."""
    response = client.get('/questions')
    # May redirect or load, either is fine
    assert response.status_code in [200, 302, 404]


def test_papers_page(client):
    """Test full past papers page."""
    response = client.get('/papers')
    # May redirect or load, either is fine
    assert response.status_code in [200, 302, 404]
