"""
Regression tests for form validators.
"""
from ahmaths import db
from ahmaths.models import Question
from ahmaths.questions.forms import MarkForm


def _seed_question(app, marks=6):
    with app.app_context():
        q = Question(
            question_id='form_test_q1',
            paper='form_test_paper',
            question_number='1',
            marks=marks,
            topics='test_topic',
            subtopics='',
        )
        db.session.add(q)
        db.session.commit()


def test_mark_form_rejects_negative(app):
    """Marks below 0 must fail validation."""
    _seed_question(app, marks=6)
    with app.test_request_context(
        method='POST',
        data={'question': 'form_test_q1', 'mark': '-1'},
    ):
        form = MarkForm()
        assert not form.validate()
        assert form.mark.errors


def test_mark_form_rejects_above_max(app):
    """Marks above the question's max mark must fail validation."""
    _seed_question(app, marks=6)
    with app.test_request_context(
        method='POST',
        data={'question': 'form_test_q1', 'mark': '7'},
    ):
        form = MarkForm()
        assert not form.validate()
        assert form.mark.errors


def test_mark_form_accepts_zero(app):
    """Mark of 0 must validate (user marked nothing right)."""
    _seed_question(app, marks=6)
    with app.test_request_context(
        method='POST',
        data={'question': 'form_test_q1', 'mark': '0'},
    ):
        form = MarkForm()
        assert form.validate(), f'Expected valid, got errors: {form.errors}'


def test_mark_form_accepts_max(app):
    """Mark equal to the question's max must validate."""
    _seed_question(app, marks=6)
    with app.test_request_context(
        method='POST',
        data={'question': 'form_test_q1', 'mark': '6'},
    ):
        form = MarkForm()
        assert form.validate(), f'Expected valid, got errors: {form.errors}'


def test_mark_form_rejects_unknown_question(app):
    """Submitting a mark for a question that doesn't exist must fail
    gracefully (not raise AttributeError)."""
    with app.test_request_context(
        method='POST',
        data={'question': 'does_not_exist', 'mark': '3'},
    ):
        form = MarkForm()
        # Validation must return False rather than blow up.
        assert not form.validate()
        assert form.mark.errors


def test_mark_form_rejects_missing_mark(app):
    """Submitting with no mark must fail validation (not crash)."""
    _seed_question(app, marks=6)
    with app.test_request_context(
        method='POST',
        data={'question': 'form_test_q1', 'mark': ''},
    ):
        form = MarkForm()
        assert not form.validate()
        assert form.mark.errors
