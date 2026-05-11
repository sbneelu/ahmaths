from flask import render_template, url_for, redirect, flash, request, Blueprint
from flask_login import current_user, login_required
from ahmaths.models import Topic, Subtopic, Question
from ahmaths.questions.forms import MarkForm
from ahmaths.questions.save_results import save_marks_to_topic, save_marks_to_progress

questions = Blueprint('questions', __name__)


@questions.route('/questions')
@login_required
def main():
    progress_strings = current_user.progress.split(',')
    progress = {}
    for progress_string in progress_strings:
        if progress_string != '':
            progress_string = progress_string.split(':')
            progress[progress_string[0]] = int(progress_string[1])
    return render_template('questions/index.html.j2', topics=Topic.query.all(), progress=progress, title='Questions by Topic')


@questions.route('/questions/<string:topic_id>')
@login_required
def topic(topic_id):
    topic = Topic.query.filter_by(topic_id=topic_id).first()
    if not topic:
        flash('Invalid topic. Please try again.', 'danger')
        return redirect(url_for('questions.main'))
    questions = Question.query.filter(Question.topics.contains(topic_id)).all()
    progress_strings = getattr(current_user, topic_id).split(',')
    progress = {}
    for progress_string in progress_strings:
        if progress_string != '':
            progress_string = progress_string.split(':')
            progress[progress_string[0]] = progress_string[1]
    return render_template('questions/question-selection.html.j2', progress=progress, questions=reversed(questions), topic=topic, title=topic.topic_name + ' | Questions by Topic')


@questions.route('/questions/question/<string:question_id>', methods=['GET', 'POST'])
@login_required
def question(question_id):
    q = Question.query.filter_by(question_id=question_id).first()
    if not q:
        flash('Invalid question. Please try again.', 'danger')
        return redirect(url_for('questions.main'))

    form = MarkForm()
    form.question.data = q.question_id
    form.mark.label.text += ' out of ' + str(q.marks)

    topic_ids = q.topics.split(',') if q.topics else []
    from_param = request.args.get('from')
    if from_param and from_param in topic_ids:
        active_topic_id = from_param
    elif topic_ids:
        active_topic_id = topic_ids[0]
    else:
        active_topic_id = None
    active_topic = Topic.query.filter_by(topic_id=active_topic_id).first() if active_topic_id else None

    if form.validate_on_submit():
        for topic_id in q.topics.split(','):
            save_marks_to_topic(topic_id, question_id, form.mark.data)
            save_marks_to_progress(topic_id)
        flash('Your marks have been recorded.', 'info')
        if active_topic:
            return redirect(url_for('questions.topic', topic_id=active_topic.topic_id))
        return redirect(url_for('questions.main'))

    subtopic_ids = q.subtopics.split(',') if q.subtopics else []

    topics = []
    subtopics = {}
    for topic_id in topic_ids:
        topic_obj = Topic.query.filter_by(topic_id=topic_id).first()
        if topic_obj:
            topics.append(topic_obj)
        for subtopic_id in subtopic_ids:
            subtopic_obj = Subtopic.query.filter_by(subtopic_id=subtopic_id).first()
            if subtopic_obj and subtopic_obj.topic_id == topic_id:
                subtopics.setdefault(topic_id, []).append(subtopic_obj)

    mark = None
    if topic_ids:
        first_topic_id = topic_ids[0]
        progress_strings = getattr(current_user, first_topic_id).split(',')
        progress = {}
        for progress_string in progress_strings:
            if progress_string != '':
                progress_string = progress_string.split(':')
                progress[progress_string[0]] = progress_string[1]
        mark = progress.get(question_id)

    show_marking = request.args.get('show_marking')
    if show_marking == 'mark_validation_error':
        flash('Invalid mark. Please scroll down and try again. Please make sure the mark is a whole number between 0 and ' + str(q.marks) + '.', 'danger')
    return render_template('questions/question.html.j2', show_marking=show_marking, question=q, topics=topics, subtopics=subtopics, mark=mark, form=form, active_topic=active_topic, title='Questions by Topic')
