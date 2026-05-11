# INSTRUCTIONS:
# 1. Create a data file in the following format:
#     PAPER NAME
#     for each question: question_no marks video topics subtopics
# 2. Run it through this file
#     - By default the script runs in --dry-run mode and prints what would be inserted.
#     - Pass --commit to insert directly into the live database via the Flask app context.
# 3. Follow the printed instructions for renaming/uploading PDFs and question screenshots.
# Comment lines start with //
# A missing data point (e.g. no video) is represented with _, e.g. 2a 6 _ differentiation implicit,parametric

import argparse
import os.path
import sys

TOPICS_AND_SUBTOPICS = {
    "partial_fractions": [
        "distinct_linear_factors",
        "repeated_linear_factor",
        "irreducible_quadratic_factor",
        "improper_rational_fraction",
    ],
    "binomial_theorem": ["binomial_coefficient", "binomial_expansion", "general_term"],
    "differentiation": [
        "new_functions",
        "chain_rule",
        "product_rule",
        "quotient_rule",
        "second_derivative",
        "parametric",
        "implicit",
        "logarithmic",
        "related_rates",
        "speed_acceleration",
    ],
    "integration": [
        "standard_integrals",
        "integration_partial_fractions",
        "substitution",
        "parts",
        "volumes_of_revolution",
    ],
    "differential_equations": [
        "first_order_variables_separable",
        "first_order_integrating_factor",
        "second_order_homogeneous",
        "second_order_non_homogeneous",
    ],
    "functions_graphs": [
        "asymptotes",
        "points_of_inflection",
        "odd_even_functions",
        "modulus_functions",
        "inverse_functions",
        "graph_sketching",
    ],
    "systems_of_equations": [
        "gaussian_elimination",
        "inconsistency_redundancy",
        "ill_conditioning",
    ],
    "complex_numbers": [
        "basic_operations",
        "polynomials_complex_roots",
        "complex_numbers_equations",
        "argand_diagrams_polar_form",
        "de_moivres_theorem",
        "loci",
    ],
    "sequences_series": [
        "arithmetic_progressions",
        "geometric_progressions",
        "summation_formulae",
    ],
    "maclaurin_series": ["simple_functions", "combining_expansions"],
    "matrices": [
        "matrix_algebra_identities",
        "determinant",
        "inverse_matrices",
        "transformation_matrices",
    ],
    "vectors": [
        "scalar_product",
        "vector_product",
        "scalar_triple_product",
        "3d_lines",
        "3d_planes",
    ],
    "methods_of_proof": [
        "direct",
        "contrapositive",
        "contradiction",
        "induction",
        "counter_example",
    ],
    "number_theory": ["euclidean_algorithm", "number_bases"],
}


def validate_topics_and_subtopics(topics_str, subtopics_str):
    topics = topics_str.split(",")
    subtopics = subtopics_str.split(",")

    invalid_topics = [
        topic for topic in topics if topic not in TOPICS_AND_SUBTOPICS.keys()
    ]
    if invalid_topics:
        return invalid_topics, []
    possible_subtopics = []
    for topic in topics:
        possible_subtopics += TOPICS_AND_SUBTOPICS[topic]
    invalid_subtopics = [
        subtopic for subtopic in subtopics if subtopic not in possible_subtopics
    ]
    return [], invalid_subtopics


def parse_input_file(filename):
    """Parse the input file. Returns (paper_id, [question_dicts])."""
    with open(filename, "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    paper_id = lines.pop(0)
    questions = []
    total_marks = 0

    for line in lines:
        if line.startswith("//"):
            continue
        line = line.replace(" _ ", "  ")
        question_no, marks, video, topics, subtopics = line.split(" ")

        invalid_topics, invalid_subtopics = validate_topics_and_subtopics(
            topics, subtopics
        )
        if invalid_topics:
            raise ValueError(f"INVALID TOPIC(S): {', '.join(invalid_topics)}")
        if invalid_subtopics:
            raise ValueError(f"INVALID SUBTOPIC(S): {', '.join(invalid_subtopics)}")

        question_id = f"{paper_id.replace(' ', '')}Q{question_no}"
        marks_int = int(marks)
        total_marks += marks_int
        questions.append({
            "question_id": question_id,
            "paper_id": paper_id,
            "question_number": question_no,
            "marks": marks_int,
            "video": video,
            "topics": topics,
            "subtopics": subtopics,
        })

    return paper_id, questions, total_marks


def write_sql_file(filename, paper_id, questions):
    """Emit the SQL file (legacy --dry-run output)."""
    sql_queries = [
        f"INSERT INTO paper (paper_id, paper_name) VALUES ('{paper_id}', '{paper_id}');"
    ]
    # Question inserts go first (matches original ordering, paper insert last).
    for q in questions:
        sql_queries.insert(
            0,
            f"INSERT INTO question (question_id, paper, question_number, marks, video, topics, subtopics) "
            f"VALUES ('{q['question_id']}', '{q['paper_id']}', '{q['question_number']}', "
            f"{q['marks']}, '{q['video']}', '{q['topics']}', '{q['subtopics']}');",
        )

    outfile_prefix = ".".join(filename.split(".")[:-1])
    while os.path.isfile(f"{outfile_prefix}.sql"):
        outfile_prefix += "_"
    outfile = f"{outfile_prefix}.sql"
    with open(outfile, "a") as f:
        for query in sql_queries:
            f.write(f"{query}\n")
    return outfile, len(sql_queries)


def commit_to_db(paper_id, questions):
    """Insert paper + questions into the live DB via Flask app context. Skips existing rows."""
    # Make sure the project root (parent of scripts/) is importable so `ahmaths`
    # resolves whether the script is invoked from the project root or scripts/.
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from ahmaths import create_app, db
    from ahmaths.models import Paper, Question

    app = create_app()
    inserted_paper = False
    inserted_questions = 0
    skipped_paper = False
    skipped_questions = 0

    with app.app_context():
        if Paper.query.filter_by(paper_id=paper_id).first() is None:
            db.session.add(Paper(paper_id=paper_id, paper_name=paper_id))
            inserted_paper = True
        else:
            skipped_paper = True

        for q in questions:
            if Question.query.filter_by(question_id=q["question_id"]).first() is None:
                db.session.add(Question(
                    question_id=q["question_id"],
                    paper=q["paper_id"],
                    question_number=q["question_number"],
                    marks=q["marks"],
                    video=q["video"],
                    topics=q["topics"],
                    subtopics=q["subtopics"],
                ))
                inserted_questions += 1
            else:
                skipped_questions += 1

        db.session.commit()

    return inserted_paper, inserted_questions, skipped_paper, skipped_questions


def print_followup(paper_id, num_queries):
    print("IMPORTANT: Make sure to do Paper 2 BEFORE Paper 1")
    print()
    print(f"STEP 1a: Name paper to `AH-Maths-{paper_id.replace(' ', '%20')}.pdf`")
    print(f"STEP 1b: Name MI to `AH-Maths-MI-{paper_id.replace(' ', '%20')}.pdf`")
    print()
    print(f"STEP 2a: Upload `AH-Maths-{paper_id.replace(' ', '%20')}.pdf` to `static/sqa-papers/papers/`")
    print(f"STEP 2b: Upload `AH-Maths-MI-{paper_id.replace(' ', '%20')}.pdf` to `static/sqa-papers/mi/`")
    print()
    print("STEP 3a: Screenshot all questions and associated MIs.")
    print("STEP 3b: Rename questions and MIs using the question IDs and upload to `static/sqa-questions/` and `static/sqa-mi/`.")
    print()
    if num_queries is not None:
        print(f"(In --dry-run mode {num_queries} SQL statements were written to disk for review.)")


def main():
    parser = argparse.ArgumentParser(
        description="Add a new paper and its questions to the database from an input file."
    )
    parser.add_argument("input_file", help="Path to the paper input file.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--commit",
        action="store_true",
        help="Insert rows directly into the live database. Existing rows are skipped.",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="(default) Print what would be inserted and emit a .sql file alongside the input.",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        print(f"File does not exist: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    try:
        paper_id, questions, total_marks = parse_input_file(args.input_file)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    if args.commit:
        inserted_paper, inserted_q, skipped_paper, skipped_q = commit_to_db(paper_id, questions)
        print(f"Paper '{paper_id}': {'inserted' if inserted_paper else 'already existed (skipped)'}")
        print(f"Questions: {inserted_q} inserted, {skipped_q} skipped (already existed)")
        print()
        print_followup(paper_id, num_queries=None)
    else:
        # Default: dry run -> write .sql file and print what would happen.
        outfile, num_queries = write_sql_file(args.input_file, paper_id, questions)
        print(f"DRY RUN: wrote {num_queries} SQL statements to `{outfile}`")
        print(f"  Paper:     {paper_id}")
        print(f"  Questions: {len(questions)} ({total_marks} marks)")
        print("  Re-run with --commit to insert into the live database instead.")
        print()
        print_followup(paper_id, num_queries)

    print()
    print(f"Sanity check: {len(questions)} questions, {total_marks} marks")


if __name__ == "__main__":
    main()
