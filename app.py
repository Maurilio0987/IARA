from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
import os
from banco_de_dados import DatabaseManager, sha256
from apscheduler.schedulers.background import BackgroundScheduler
import requests



app = Flask(__name__)
app.secret_key = 'chave_secreta'  


db_url = "mysql://root:ajNlmcyIPZQVSGsTkLXFRDjmpkNzkQTw@hopper.proxy.rlwy.net:22040/railway"
db = DatabaseManager(db_url)

BASE_URL = "http://10.180.0.100:8123/api/states"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI1MWFiZWY2ZTIyOWU0YjY5YTliNjc0NWU1MzhiZTI2NyIsImlhdCI6MTc0NTMyNTU3MywiZXhwIjoyMDYwNjg1NTczfQ.o07Qigaa-TOlNp1HFLBSzXYpMmVX0qOXZWl-WWASjKw"

# Cabeçalhos
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Sensores que queremos pegar
sensor_ids = {
    "sensor.vento_kmh": "velocidade_vento",
    "sensor.direzione_vento": "direcao_vento",
    "sensor.precipitacao_mm": "precipitacao",
    "sensor.tasmota_am2301_temperature": "temperatura",
    "sensor.tasmota_am2301_humidity": "umidade"
}

#scheduler = BackgroundScheduler()
#scheduler.add_job(db.atualizar_hortas, "cron", hour=0, minute=0, second=0)
#scheduler.start()


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
    if email == "admin@admin" and senha == "admin":
        session["email"] = email
        return redirect(url_for("admin"))
        
        
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
    return render_template("horta.html")


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


@app.route("/esp32/estado/<chave>")
def estado(chave):
    estado = {"estado": db.estado(chave)}
    return jsonify(estado)


@app.route("/estacao")
def estacao():
    try:
        response = requests.get(BASE_URL, headers=headers)
        response.raise_for_status()

        dados = response.json()
        resultado = {}

        for sensor in dados:
            eid = sensor.get("entity_id")
            if eid in sensor_ids:
                resultado[sensor_ids[eid]] = sensor.get("state")

        return jsonify(resultado)

    except requests.exceptions.RequestException as e:
        print("Erro ao conectar com o Home Assistant:", e)
        return jsonify({})


@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html")


@app.route("/admin/culturas")
@login_required
def culturas():
    tabela = db.tabela("culturas")
    return render_template("culturas.html", tabela=tabela)
    

@app.route("/admin/solos")
@login_required
def solos():
    tabela = db.tabela("solos")
    return render_template("solos.html", tabela=tabela)


@app.route("/admin/adicionar_solo", methods=["POST"])
def adicionar_solo():
    nome = request.form["nome"]
    capacidade_campo = request.form["capacidade_campo"]
    ponto_murcha = request.form["ponto_murcha"]
    densidade = request.form["densidade"]
    porosidade = request.form["porosidade"]
    cond_hidraulica = request.form["cond_hidraulica"]
    
    db.adicionar_solo(nome, capacidade_campo, ponto_murcha, densidade, porosidade, cond_hidraulica)
    return redirect(url_for("admin/solos"))
    
    
#@app.route("/dados")
#def dados():
#    return jsonify(banco_de_dados)
    
    
#@app.route("/umidade", methods=["POST"])
#def umidade():
#    banco_de_dados["umidade"] = request.get_json()["umidade"]
#    return {"status": "Sucesso"}, 200


#app.run(debug=True, host="localhost")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
