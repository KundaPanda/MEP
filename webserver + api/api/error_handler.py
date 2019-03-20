from flask import render_template, url_for, Blueprint

blueprint = Blueprint("error_handlers", __name__)


@blueprint.app_errorhandler(400)
def bad_request(dump):
    return (
        render_template(
            "index.html",
            body="400 Bad request",
            image=url_for("static", filename="400.jpg"),
        ),
        400,
    )


@blueprint.app_errorhandler(401)
def unauthorized(dump):
    return (
        render_template(
            "index.html",
            body="401 Unauthorized",
            image=url_for("static", filename="401.jpg"),
        ),
        401,
    )


@blueprint.app_errorhandler(403)
def forbidden(dump):
    return (
        render_template(
            "index.html",
            body="403 Forbidden",
            image=url_for("static", filename="403.jpg"),
        ),
        403,
    )


@blueprint.app_errorhandler(404)
def not_found(dump):
    return (
        render_template(
            "index.html",
            body="404 Not found",
            image=url_for("static", filename="404.jpg"),
        ),
        404,
    )


@blueprint.app_errorhandler(405)
def method_not_allowed(dump):
    return (
        render_template(
            "index.html",
            body="405 Method not allowed",
            image=url_for("static", filename="405.jpg"),
        ),
        405,
    )


@blueprint.app_errorhandler(417)
def method_not_allowed(dump):
    return (
        render_template(
            "index.html",
            body="417 Expectation failed",
            image=url_for("static", filename="417.jpg"),
        ),
        417,
    )


@blueprint.app_errorhandler(418)
def method_not_allowed(dump):
    return (
        render_template(
            "index.html",
            body="418 I'm a teapot :)",
            image=url_for("static", filename="418.jpg"),
        ),
        418,
    )


@blueprint.app_errorhandler(500)
def method_not_allowed(dump):
    return (
        render_template(
            "index.html",
            body="500 Internal server error",
            image=url_for("static", filename="500.jpg"),
        ),
        500,
    )
