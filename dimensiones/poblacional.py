from flask import Blueprint, render_template

bp = Blueprint("poblacional", __name__)   # cambia el nombre en cada archivo


@bp.route("/poblacional")
def poblacional():
    return render_template("poblacional.html")