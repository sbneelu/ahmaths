from flask import render_template, Blueprint

errors = Blueprint('errors', __name__)


@errors.app_errorhandler(404)
def error_404(error):
    return render_template('errors/404.html.j2', title='Page not found'), 404


@errors.app_errorhandler(500)
def error_500(error):
    return render_template('errors/500.html.j2', title='Internal server error'), 500
