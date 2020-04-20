from flask import render_template, Blueprint
from ahmaths.models import Paper

revise = Blueprint('revise', __name__)


@revise.route('/revise')
def main():
    papers = Paper.query.all()
    papers.reverse()
    return render_template('revise/index.html.j2', papers=papers, title='Revise')
