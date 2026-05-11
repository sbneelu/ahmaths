from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, HiddenField
from wtforms.validators import DataRequired, ValidationError
from ahmaths.models import Question


class MarkForm(FlaskForm):
    question = HiddenField('Question')
    mark = IntegerField('Mark')
    submit = SubmitField('Submit')

    def validate_mark(self, mark):
        q = Question.query.filter_by(question_id=self.question.data).first()
        if q is None:
            raise ValidationError('Invalid question. Please reload the page and try again.')
        max_mark = int(q.marks)
        if mark.data is None:
            raise ValidationError(f'Mark must be between 0 and {max_mark}.')
        if not 0 <= mark.data <= max_mark:
            raise ValidationError(f'Mark must be between 0 and {max_mark}.')
