from ahmaths import create_app, db
from ahmaths.models import Topic, Subtopic, Question, Paper, User

app = create_app()


def setup_db(db, app):

    with app.app_context():
        db.session.add(Paper(paper_name='2019 Paper', paper_id='2019'))
        db.session.add(Question(marks=10, question_id='2019Q18', question_number='18', video='pSY2F72ajFw?start=0', paper='2019', topics='complex_numbers'))
        db.session.add(Question(marks=10, question_id='2019Q17', question_number='17', video='uaeBWpLsVrg?start=0', paper='2019', topics='sequences_series'))
        db.session.add(Question(marks=8, question_id='2019Q16', question_number='16', video='QJU6EKlCwWw?start=0', paper='2019', topics='integration', subtopics='parts,volumes_of_revolution'))
        db.session.add(Question(marks=9, question_id='2019Q15', question_number='15', video='K7eIFGNRwpE?start=0', paper='2019', topics='vectors'))
        db.session.add(Question(marks=5, question_id='2019Q14', question_number='14', video='TPf-e3390po?start=0', paper='2019', topics='methods_of_proof', subtopics='induction'))
        db.session.add(Question(marks=5, question_id='2019Q13', question_number='13', video='7qO-7PCaz5w?start=0', paper='2019', topics='differential_equations'))
        db.session.add(Question(marks=3, question_id='2019Q12', question_number='12', video='dNazvIOPiUA?start=0', paper='2019', topics='number_theory', subtopics='number_bases,euclidean_algorithm'))
        db.session.add(Question(marks=5, question_id='2019Q11', question_number='11', video='0GDca77OuJs?start=0', paper='2019', topics='methods_of_proof', subtopics='counter_example,contrapositive'))
        db.session.add(Question(marks=5, question_id='2019Q10', question_number='10', video='wr7X5YHIDFw?start=0', paper='2019', topics='differentiation', subtopics='implicit,chain_rule'))
        db.session.add(Question(marks=5, question_id='2019Q9', question_number='9', video='Avasghf2TcM?start=0', paper='2019', topics='binomial_theorem', subtopics='general_term'))
        db.session.add(Question(marks=5, question_id='2019Q8', question_number='8', video='QizQ2YdlIP4?start=0', paper='2019', topics='differential_equations'))
        db.session.add(Question(marks=3, question_id='2019Q7', question_number='7', video='9Ij2GpMo9dI?start=0', paper='2019', topics='sequences_series'))
        db.session.add(Question(marks=3, question_id='2019Q6', question_number='6', video='_c92QdBS1sU?start=0', paper='2019', topics='differentiation', subtopics='related_rates'))
        db.session.add(Question(marks=4, question_id='2019Q5', question_number='5', video='Ey16SO6AjXE?start=0', paper='2019', topics='differentiation', subtopics='parametric,second_derivative'))
        db.session.add(Question(marks=4, question_id='2019Q4', question_number='4', video='dThtzIfdDsc?start=0', paper='2019', topics='partial_fractions', subtopics='improper_rational_fraction,distinct_linear_factors'))
        db.session.add(Question(marks=2, question_id='2019Q3', question_number='3', video='HD7MX6QiYGc?start=0', paper='2019', topics='functions_graphs'))
        db.session.add(Question(marks=6, question_id='2019Q2', question_number='2', video='LIy0Aj6BPI0?start=0', paper='2019', topics='matrices'))
        db.session.add(Question(marks=3, question_id='2019Q1c', question_number='1c', video='YQfhwzO_2io?start=200', paper='2019', topics='differentiation', subtopics='new_functions,chain_rule'))
        db.session.add(Question(marks=3, question_id='2019Q1b', question_number='1b', video='YQfhwzO_2io?start=101', paper='2019', topics='differentiation', subtopics='quotient_rule'))
        db.session.add(Question(marks=2, question_id='2019Q1a', question_number='1a', video='YQfhwzO_2io?start=0', paper='2019', topics='differentiation', subtopics='product_rule,new_functions'))

        db.session.commit()


setup_db(db, app)
