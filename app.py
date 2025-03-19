from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
import os


app = Flask(__name__)
app.secret_key = 'chave_secreta'  


logins = {"admin@admin": "1234",
          "flaviomaurilio0@gmail.com": "4321"}


def login_required(f):
    @wraps(f)  # mantém o nome e docstring da função original (boa prática)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:  # verifica se o usuário está na session (se está logado)
            return redirect(url_for('index'))  # se não estiver, redireciona para /login
        return f(*args, **kwargs)  # se estiver, executa a função da rota normalmente
    return decorated_function


@app.route("/")
def index():
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
    return f"bem vindo {session['email']} <br><br> <a href='logout'>logout</a>"
    

    


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
          
#app.run(debug=True, host="localhost", port=80)
