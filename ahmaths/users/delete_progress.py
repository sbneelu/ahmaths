from flask_login import current_user
from ahmaths import db
from ahmaths.models import Question
from ahmaths.practise.save_results import save_marks_to_progress


def delete_topic_progress(topic_id):
    progress_strings = getattr(current_user, topic_id).split(',')
    questions = []
    for progress_string in progress_strings:
        if progress_string != '':
            question_id, mark = progress_string.split(':')
            questions.append(question_id)

    topics_modified = [topic_id]

    for question_id in questions:
        question = Question.query.filter_by(question_id=question_id).first()
        topics = question.topics.split(',')
        if len(topics) > 1:
            for topic in topics:
                delete_question_from_topic(question_id, topic)
                if topic not in topics_modified:
                    topics_modified.append(topic)

    setattr(current_user, topic_id, '')
    db.session.commit()
    for topic in topics_modified:
        save_marks_to_progress(topic)


def delete_question_from_topic(question_id, topic_id):
    progress_strings = getattr(current_user, topic_id).split(',')
    progress = {}
    for progress_string in progress_strings:
        if progress_string != '':
            progress_string = progress_string.split(':')
            if progress_string[0] != question_id:
                progress[progress_string[0]] = progress_string[1]
    progress_strings = ''
    for key, value in progress.items():
        progress_strings += key + ':' + str(value) + ','
    progress_strings = progress_strings[:-1]
    setattr(current_user, topic_id, progress_strings)
    db.session.commit()
