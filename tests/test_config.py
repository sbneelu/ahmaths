"""
Tests for configuration management.
"""
import os
import pytest


def test_config_from_environment(app):
    """Test that config loads from environment variables."""
    assert app.config['SECRET_KEY'] == 'test-secret-key-for-testing-only'
    assert 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']


def test_config_testing_mode(app):
    """Test that app is in testing mode."""
    assert app.config['TESTING'] is True


def test_sqlalchemy_track_modifications_disabled(app):
    """Test that SQLALCHEMY_TRACK_MODIFICATIONS is disabled."""
    # This should be False to suppress warnings
    assert app.config.get('SQLALCHEMY_TRACK_MODIFICATIONS', True) is False
