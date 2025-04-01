from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
import os
from banco_de_dados import DatabaseManager, sha256





app = Flask(__name__)
app.secret_key = 'chave_secreta'  


db_url = "mysql://root:ajNlmcyIPZQVSGsTkLXFRDjmpkNzkQTw@hopper.proxy.rlwy.net:22040/railway"
db = DatabaseManager(db_url)


@app.route("/sobre")
def sobre():
    return render_template("sobre.html")


@app.route("/contato")
def contato():
    return render_template("contato.html")
    

@app.route("/ajuda")
def ajuda():
    return render_template("ajuda.html")
    

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    if session.get("email"): return redirect(url_for("hortas"))
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    senha = request.form["password"]
    if db.verificar_email(email):
        if db.verificar_senha(email, sha256(senha)):
            session["email"] = email
            return redirect(url_for("hortas"))
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    session.pop("email", None)
    return redirect(url_for("index"))


@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")


@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    email = request.form["email"]
    senha = request.form["password"]
    if not db.verificar_email(email):
        db.adicionar_usuario(email, sha256(senha))
        return redirect(url_for("index"))
    return redirect(url_for("cadastro"))


@app.route("/hortas")
@login_required
def hortas():
    culturas = db.culturas()
    solos = db.solos()
    return render_template("hortas.html", solos=solos, culturas=culturas)
   
   
@app.route("/hortas/<chave>")
@login_required
def horta(chave):
    return "Página da horta"


@app.route("/cadastrar_horta", methods=["POST"])
def cadastrar_horta():
    dados = request.json
    tamanho = dados.get("tamanho")
    cultura = dados.get("cultura")
    solo = dados.get("solo")
    tempo = int(dados.get("tempo"))
    usuario = db.usuario(session["email"])
    db.adicionar_horta(usuario, tamanho, cultura, solo, tempo)
    
    return {"status": "Sucesso"}, 200


@app.route("/atualizar_hortas")
def atualizar_hortas():
    return jsonify(db.hortas(session["email"]))


#@app.route("/dados")
#def dados():
#    return jsonify(banco_de_dados)
    
    
#@app.route("/umidade", methods=["POST"])
#def umidade():
#    banco_de_dados["umidade"] = request.get_json()["umidade"]
#    return {"status": "Sucesso"}, 200


app.run(debug=True, host="localhost", port=80)

#if __name__ == "__main__":
#    port = int(os.environ.get("PORT", 5000))
#    app.run(host="0.0.0.0", port=port)
