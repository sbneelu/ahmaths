import re
from flask import render_template, Blueprint
from ahmaths.models import Paper

papers = Blueprint('papers', __name__)


def _paper_sort_key(paper):
    """Sort papers newest first, Paper 1 before Paper 2, specimens at the end."""
    paper_id = paper.paper_id or ''
    is_specimen = 'specimen' in paper_id.lower()
    year_match = re.search(r'(\d{4})', paper_id)
    year = int(year_match.group(1)) if year_match else 0
    paper_num_match = re.search(r'Paper\s*(\d)', paper_id)
    paper_num = int(paper_num_match.group(1)) if paper_num_match else 0
    return (is_specimen, -year, paper_num)


@papers.route('/papers')
def main():
    all_papers = Paper.query.all()
    all_papers.sort(key=_paper_sort_key)
    return render_template('papers/index.html.j2', papers=all_papers, title='Full Past Papers')
