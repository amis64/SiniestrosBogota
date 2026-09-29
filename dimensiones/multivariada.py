from flask import Blueprint, render_template

bp = Blueprint("multivariada", __name__) 

@bp.route("/multivariada")
def multivariada():
    return render_template("multivariada.html")