from flask import Flask, render_template

from dimensiones.poblacional import bp as poblacional_bp
from dimensiones.territorial import bp as territorial_bp
from dimensiones.temporal import bp as temporal_bp
from dimensiones.multivariada import bp as multivariada_bp

app = Flask(__name__)

app.register_blueprint(poblacional_bp)
app.register_blueprint(territorial_bp)
app.register_blueprint(temporal_bp)
app.register_blueprint(multivariada_bp)


@app.route("/")
def inicio():
    return render_template("inicio.html")


if __name__ == "__main__":
    app.run(debug=True)