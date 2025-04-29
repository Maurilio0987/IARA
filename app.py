from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
import os
from banco_de_dados import DatabaseManager, sha256
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import math


app = Flask(__name__)
app.secret_key = 'chave_secreta'  


db_url = "mysql://root:ajNlmcyIPZQVSGsTkLXFRDjmpkNzkQTw@hopper.proxy.rlwy.net:22040/railway"
db = DatabaseManager(db_url)

BASE_URL = "http://10.180.0.100:8123/api/states"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI1MWFiZWY2ZTIyOWU0YjY5YTliNjc0NWU1MzhiZTI2NyIsImlhdCI6MTc0NTMyNTU3MywiZXhwIjoyMDYwNjg1NTczfQ.o07Qigaa-TOlNp1HFLBSzXYpMmVX0qOXZWl-WWASjKw"


headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

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


#                 #
#-----FUNÇÕES-----#
#                 #


def calcular_eto(T, RH, u2, Rs_Wm2):
	"""
     Calcula ET0 simplificado (mm/dia) usando apenas
     temperatura média (T, °C), umidade (%) ,
     velocidade do vento u2 (m/s) e radiação Rs (W/m²).
	"""
	# 1) Radiação líquida (MJ/m²·dia)
	Rs = Rs_Wm2 * 0.0864  # 1 W/m² = 0.0864 MJ/m²·dia
	albedo = 0.23
	Rn = (1 - albedo) * Rs  # MJ/m²·dia

	# 2) Pressões de vapor
	es = 0.6108 * math.exp((17.27 * T) / (T + 237.3))  # kPa
	ea = (RH / 100.0) * es  # kPa

	# 3) Declive da curva de vapor
	delta = (4098 * es) / ((T + 237.3) ** 2)  # kPa/°C

	# 4) Constante psicrométrica fixa
	gamma = 0.066  # kPa/°C

	# 5) Equação simplificada de Penman-Monteith
	Eto = (
				  0.408 * delta * Rn
				  + gamma * (900.0 / (T + 273.0)) * u2 * (es - ea)
		  ) / (delta + gamma * (1 + 0.34 * u2))

	return Eto


def dados_meteorologicos():
    latitude = -5.6622
    longitude = -37.7989

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}"
        f"&current=temperature_2m,relative_humidity_2m,shortwave_radiation,wind_speed_10m"
    )

    res = requests.get(url)

    if res.status_code == 200:
        dados = res.json()["current"]
        temperatura = f"{dados['temperature_2m']} °C"
        umidade = f"{dados['relative_humidity_2m']} %"
        radiacao_solar = f"{dados['shortwave_radiation']} W/m²"
        velocidade_10m = dados['wind_speed_10m']

        velocidade_2m = velocidade_10m * (4.87 / math.log(67.8 * 10 - 5.42))
        velocidade_vento_2m = f"{velocidade_2m:.2f} km/h"

        return {
            "temperatura": temperatura,
            "umidade": umidade,
            "radiacao_solar": radiacao_solar,
            "vento": velocidade_vento_2m
        }
    else:
        return {
            "temperatura": "---",
            "umidade": "---",
            "radiacao_solar": "---",
            "vento": "---"}

"""
    response = requests.get(BASE_URL, headers=headers)
    response.raise_for_status()

    dados_home = response.json()
    resultado = {}

    for sensor in dados_home:
        eid = sensor.get("entity_id")
        if eid in sensor_ids:
            resultado[sensor_ids[eid]] = sensor.get("state")

    resposta = {
        "precipitacao": resultado["precipitacao"],
        "vento": float(resultado["velocidade_vento"]) * 3.6,
        "direcao": resultado["direcao_vento"],
        "temperatura": resultado["temperatura"],
        "umidade": resultado["umidade"]
    }

    temperatura = resposta["temperatura"]
    velocidade_vento = resposta["vento"]
"""

def calcular_consumo(kc, area):
    eto = calcular_eto()
    etc = eto * kc
    consumo = etc * area
    return {"eto": eto,
            "etc": etc,
            "consumo": consumo}


#                  #
#-----ESTÁTICO-----#
#                  #


@app.route("/sobre")
def sobre():
    return render_template("sobre.html")


@app.route("/contato")
def contato():
    return render_template("contato.html")
    

@app.route("/ajuda")
def ajuda():
    return render_template("ajuda.html")


#               #   
#-----LOGIN-----#
#               #


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


#                #   
#-----HORTAS-----#
#                #


@app.route("/hortas")
@login_required
def hortas():
    culturas = db.culturas()
    solos = db.solos()
    return render_template("hortas.html", solos=solos, culturas=culturas)
   
   
@app.route("/hortas/<chave>")
@login_required
def horta(chave):
    horta = db.horta(chave)
    return render_template("horta.html", horta={
        "nome": horta[1],
        "planta": horta[3],
        "solo": horta[4],
        "estagio": horta[6],
        "tempo": horta[7],
        "area": horta[2]
    },
    clima={
        "temperatura": "---",
        "umidade": "---",
        "vento": "---",
        "radiacao": "---",
        "eto": "---",
    },
    gasto={
        "etc": "---",
        "volume": "---"
    })


@app.route("/cadastrar_horta", methods=["POST"])
def cadastrar_horta():
    dados = request.json
    nome = dados.get("nome")
    tamanho = dados.get("tamanho")
    cultura = dados.get("cultura")
    solo = dados.get("solo")
    tempo = int(dados.get("tempo"))
    usuario = db.usuario(session["email"])
    db.adicionar_horta(usuario, nome, tamanho, cultura, solo, tempo)
    
    return {"status": "Sucesso"}, 200


@app.route("/atualizar_hortas")
def atualizar_hortas():
    return jsonify(db.hortas(session["email"]))


@app.route("/esp32/estado/<chave>")
def estado(chave):
    estado = {"estado": db.estado(chave)}
    return jsonify(estado)


@app.route("/consumo/<chave>")
def consumo(chave):
    horta = db.horta(chave)
    kc = horta[8]
    area = horta[2]

    return jsonify(calcular_consumo(kc, area))


#                 #
#-----ESTAÇÃO-----#
#                 #


@app.route("/estacao")
def estacao():
    return jsonify(dados_meteorologicos())


#             #
#-----ADM-----#
#             #


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


#app.run(debug=True, host="localhost", port=80)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
