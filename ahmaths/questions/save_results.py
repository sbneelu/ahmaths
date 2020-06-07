from flask_login import current_user
from ahmaths import db
from ahmaths.models import Question


def save_marks_to_topic(topic_id, question_id, mark):
    progress_strings = getattr(current_user, topic_id).split(',')
    progress = {}
    for progress_string in progress_strings:
        if progress_string != '':
            progress_string = progress_string.split(':')
            progress[progress_string[0]] = progress_string[1]
    progress[question_id] = mark
    progress_strings = ''
    for key, value in progress.items():
        progress_strings += key + ':' + str(value) + ','
    progress_strings = progress_strings[:-1]
    setattr(current_user, topic_id, progress_strings)
    db.session.commit()


def save_marks_to_progress(topic_id):
    progress_strings = current_user.progress.split(',')
    progress = {}
    for progress_string in progress_strings:
        if progress_string != '':
            progress_string = progress_string.split(':')
            progress[progress_string[0]] = progress_string[1]
    questions = Question.query.filter(Question.topics.contains(topic_id)).all()
    max_marks = 0
    for question in questions:
        max_marks += question.marks
    mark = 0
    questions = getattr(current_user, topic_id).split(',')
    for question in questions:
        if question:
            mark += int(question.split(':')[1])
    percentage = round(mark / max_marks * 100)
    progress[topic_id] = str(percentage)
    progress_strings = ''
    for key, value in progress.items():
        progress_strings += key + ':' + value + ','
    setattr(current_user, 'progress', progress_strings)
    db.session.commit()
