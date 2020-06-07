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
    if Topic.query.filter_by(topic_id=topic_id).first():
        topic = Topic.query.filter_by(topic_id=topic_id).first()
        questions = Question.query.filter(Question.topics.contains(topic_id)).all()
        progress_strings = getattr(current_user, topic_id).split(',')
        progress = {}
        for progress_string in progress_strings:
            if progress_string != '':
                progress_string = progress_string.split(':')
                progress[progress_string[0]] = progress_string[1]
        return render_template('questions/question-selection.html.j2', progress=progress, questions=reversed(questions), topic=topic, title=topic.topic_name + ' | Questions by Topic')
    else:
        flash('Invalid topic. Please try again.', 'danger')
        return redirect(url_for('questions.main'))


@questions.route('/questions/question/<string:question_id>', methods=['GET', 'POST'])
@login_required
def question(question_id):
    if Question.query.filter_by(question_id=question_id).first():
        q = Question.query.filter_by(question_id=question_id).first()
        form = MarkForm()
        form.question.data = q.question_id
        form.mark.label.text += ' out of ' + str(q.marks)
        if form.validate_on_submit():
            topics = q.topics.split(',')
            for topic in topics:
                save_marks_to_topic(topic, question_id, form.mark.data)
                save_marks_to_progress(topic)
            flash('Your marks have been recorded.', 'info')
            return redirect(url_for('questions.main'))
        q = Question.query.filter_by(question_id=question_id).first()
        topics = []
        subtopics = {}
        for topic in q.topics.split(','):
            topics += [Topic.query.filter_by(topic_id=topic).first()]
            for subtopic in q.subtopics.split(','):
                if Subtopic.query.filter_by(subtopic_id=subtopic).first() and Subtopic.query.filter_by(subtopic_id=subtopic).first().topic_id == topic:
                    if topic not in subtopics:
                        subtopics[topic] = []
                    subtopics[topic] += [Subtopic.query.filter_by(subtopic_id=subtopic).first()]

        progress_strings = getattr(current_user, topic).split(',')
        progress = {}
        for progress_string in progress_strings:
            if progress_string != '':
                progress_string = progress_string.split(':')
                progress[progress_string[0]] = progress_string[1]
        mark = progress[question_id] if question_id in progress else None
        show_marking = request.args.get('show_marking')
        if show_marking == 'mark_validation_error':
            flash('Invalid mark. Please scroll down and try again. Please make sure the mark is a whole number between 0 and ' + str(q.marks) + '.', 'danger')
        return render_template('questions/question.html.j2', show_marking=show_marking, question=q, topics=topics, subtopics=subtopics, mark=mark, form=form, title='Questions by Topic')
    else:
        flash('Invalid question. Please try again.', 'danger')
        return redirect(url_for('questions.main'))
