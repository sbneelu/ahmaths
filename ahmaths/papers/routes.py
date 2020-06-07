from flask import render_template, Blueprint
from ahmaths.models import Paper

papers = Blueprint('papers', __name__)


@papers.route('/papers')
def main():
    papers = Paper.query.all()
    papers.reverse()
    return render_template('papers/index.html.j2', papers=papers, title='Full Past Papers')
