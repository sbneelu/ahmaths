from flask import render_template, url_for, redirect, flash, Blueprint
from ahmaths.models import Topic, Subtopic, Question

learn = Blueprint('learn', __name__)


@learn.route('/learn')
def main():
    topics = Topic.query.all()
    return render_template('learn/index.html.j2', topics=topics, title='Learn')


@learn.route('/learn/<string:topic_id>')
def topic(topic_id):
    topic = Topic.query.filter_by(topic_id=topic_id).first()
    if topic:
        return render_template('learn/topics/' + topic.topic_id + '/index.html.j2', topic=topic, title=topic.topic_name + ' | Learn')
    else:
        flash('Invalid topic. Please try again.', 'danger')
        return redirect(url_for('learn.main'))


@learn.route('/learn/<string:topic_id>/<string:subtopic_id>')
def subtopic(topic_id, subtopic_id):
    topic = Topic.query.filter_by(topic_id=topic_id).first()
    if topic:
        subtopic = Subtopic.query.filter_by(subtopic_id=subtopic_id).first()
        if subtopic and subtopic.topic.topic_id == topic_id:
            questions = Question.query.filter(Question.subtopics.contains(subtopic_id)).all()
            questions.reverse()
            return render_template('learn/topics/' + topic.topic_id + '/' + subtopic.subtopic_id + '.html.j2', topic=topic, subtopic=subtopic, questions=questions, title=subtopic.subtopic_name + ' | Learn')
        else:
            flash('Invalid subtopic. Please try again.', 'danger')
            return redirect(url_for('learn.topic', topic_id=topic_id))
    else:
        flash('Invalid topic. Please try again.', 'danger')
        return redirect(url_for('learn.main'))
