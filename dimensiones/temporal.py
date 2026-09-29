from flask import Blueprint, render_template

bp = Blueprint("temporal", __name__)  


@bp.route("/temporal")
def temporal():
    return render_template("temporal.html")