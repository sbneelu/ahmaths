# INSTRUCTIONS:
# 1. Create a data file in the following format:
#     PAPER NAME
#     for each question: question_no marks video topics subtopics
# 2. Run it through this file
# 3. Follow the printed instructions
# Comment lines start with //
# A missing data point (e.g. no video) is represented with _, e.g. 2a 6 _ differentiation implicit,parametric

from sys import argv
import os.path

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


def main(args):
    if len(args) != 1:
        print("Usage: python3 add_new_paper_to_db.py <input file>")
        return
    filename = args[0]
    if not os.path.isfile(filename):
        print("File does not exist")
        return
    with open(filename, "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    sql_queries = []

    paper_id = lines.pop(0)
    sql_queries.append(
        f"INSERT INTO paper (paper_id, paper_name) VALUES ('{paper_id}', '{paper_id}');"
    )

    total_questions = total_marks = 0

    for line in lines:
        if line.startswith("//"):
            continue
        line = line.replace(" _ ", "  ")
        question_no, marks, video, topics, subtopics = line.split(" ")

        invalid_topics, invalid_subtopics = validate_topics_and_subtopics(
            topics, subtopics
        )

        if invalid_topics:
            print(f"INVALID TOPIC(S): {', '.join(invalid_topics)}")
            return
        if invalid_subtopics:
            print(f"INVALID SUBTOPIC(S): {', '.join(invalid_subtopics)}")
            return

        question_id = f"{paper_id.replace(' ', '')}Q{question_no}"

        sql_queries.insert(0, 
            f"INSERT INTO question (question_id, paper, question_number, marks, video, topics, subtopics) "
            f"VALUES ('{question_id}', '{paper_id}', '{question_no}', {marks}, '{video}', '{topics}', '{subtopics}');"
        )

        total_questions += 1
        total_marks += int(marks)

    outfile_prefix = ".".join(filename.split(".")[:-1])
    while os.path.isfile(f"{outfile_prefix}.sql"):
        outfile_prefix += "_"
    outfile = f"{outfile_prefix}.sql"
    with open(outfile, "a") as f:
        for query in sql_queries:
            f.write(f"{query}\n")

    print("IMPORTANT: Make sure to do Paper 2 BEFORE Paper 1")
    print()
    print(f"STEP 1a: Name paper to `AH-Maths-{paper_id.replace(' ', '%20')}.pdf`")
    print(f"STEP 1b: Name MI to `AH-Maths-MI-{paper_id.replace(' ', '%20')}.pdf`")
    print()
    print(
        f"STEP 2a: Upload `AH-Maths-{paper_id.replace(' ', '%20')}.pdf` to `static/sqa-papers/papers/`"
    )
    print(
        f"STEP 2b: Upload `AH-Maths-MI-{paper_id.replace(' ', '%20')}.pdf` to `static/sqa-papers/mi/`"
    )
    print()
    print(f"STEP 3a: Screenshot all questions and associated MIs.")
    print(f"STEP 3b: Rename questions and MIs using the question IDs in `{outfile}` and upload to `static/sqa-questions/` and `static/sqa-mi/`.")
    print()
    print(f"STEP 4: Run the {len(sql_queries)} database queries in `{outfile}`.")
    print()
    print(f"Sanity check: {total_questions} questions, {total_marks} marks")


if __name__ == "__main__":
    main(argv[1:])
