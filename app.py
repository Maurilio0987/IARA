from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
import os


app = Flask(__name__)
app.secret_key = 'chave_secreta'  


logins = {"admin@admin": "1234",
          "flaviomaurilio0@gmail.com": "4321"}

banco_de_dados = {"umidade": 0}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    if session.get("email"): return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    senha = request.form["password"]
    if email in logins and senha == logins[email]:
        session["email"] = email
        return redirect(url_for("dashboard"))
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    session.pop("email", None)
    return redirect(url_for("index"))

    
@app.route("/sobre")
def sobre():
    return render_template("sobre.html")


@app.route("/contato")
def contato():
    return render_template("contato.html")
    

@app.route("/ajuda")
def ajuda():
    return render_template("ajuda.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")
    

@app.route("/dados")
def dados():
    return jsonify(banco_de_dados)
    
    
@app.route("/umidade", methods=["POST"])
def umidade():
    banco_de_dados["umidade"] = request.get_json()["umidade"]
    return {"status": "recebido"}, 200


#app.run(debug=True, host="localhost", port=80)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
