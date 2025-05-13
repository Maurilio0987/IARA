from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
import os
from banco_de_dados import DatabaseManager, sha256
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import math
from pytz import timezone



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




#                 #
#-----FUNÇÕES-----#
#                 #


def calcular_eto(temperatura_C, umidade_relativa, velocidade_vento_m_s, radiacao_solar_W_m2):
    radiacao_solar_MJ_m2_dia = radiacao_solar_W_m2 * 0.0864
    albedo_cultivo = 0.23
    radiacao_liquida = (1 - albedo_cultivo) * radiacao_solar_MJ_m2_dia

    pressao_vapor_saturado = 0.6108 * math.exp((17.27 * temperatura_C) / (temperatura_C + 237.3))
    pressao_vapor_real = (umidade_relativa / 100.0) * pressao_vapor_saturado

    declividade_curva_pressao_vapor = (4098 * pressao_vapor_saturado) / ((temperatura_C + 237.3) ** 2)
    constante_psicrometrica = 0.066  # valor típico

    eto = (
        0.408 * declividade_curva_pressao_vapor * radiacao_liquida
        + constante_psicrometrica * (900.0 / (temperatura_C + 273.0)) * velocidade_vento_m_s * (pressao_vapor_saturado - pressao_vapor_real)
    ) / (declividade_curva_pressao_vapor + constante_psicrometrica * (1 + 0.34 * velocidade_vento_m_s))

    return round(eto, 2)


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
        temperatura = f"{dados['temperature_2m']}"
        umidade = f"{dados['relative_humidity_2m']}"
        radiacao_solar = f"{dados['shortwave_radiation']}"
        velocidade_10m = dados['wind_speed_10m']

        velocidade_2m = velocidade_10m * (4.87 / math.log(67.8 * 10 - 5.42))
        velocidade_vento_2m = f"{velocidade_2m:.2f}"

        return {
            "temperatura": float(temperatura),
            "umidade": float(umidade),
            "radiacao_solar": float(radiacao_solar),
            "vento": float(velocidade_vento_2m)
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

def calcular_consumo(chave):    
    horta = db.horta(chave)
    kc = horta[8]
    area = horta[2]


    dados = dados_meteorologicos()
    if dados["temperatura"] == "---": return {"eto": "---",
                                             "etc": "---",
                                             "consumo": "---"} 
    temperatura = dados["temperatura"]
    umidade = dados["umidade"]
    rad_solar = dados["radiacao_solar"]
    velocidade_vento = dados["vento"]
    
    
    eto = calcular_eto(temperatura, umidade, velocidade_vento, rad_solar)
    etc = eto * kc
    consumo = etc * area
    
    return {"eto": eto,
            "etc": etc,
            "consumo": round(consumo/24, 2)}


def atualizar_volumes():
    chaves = db.chaves()
    for chave in chaves:            
        consumo = calcular_consumo(chave)
        if consumo["consumo"] == "---": consumo["consumo"] = 0
        db.adicionar_volume(chave, consumo["consumo"])









#scheduler = BackgroundScheduler(timezone=timezone("America/Sao_Paulo"))
#scheduler.add_job(atualizar_volumes, "cron", minute=0, id="volume_por_hora")
#scheduler.add_job(db.zerar_volumes, "cron", hour=0, minute=0, second=0, id="zerar_volumes_diario")
#scheduler.add_job(db.atualizar_hortas, "cron", hour=0, minute=0, second=0, id="atualizar_hortas_diario")
#scheduler.start()



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
    if session.get("email") == "admin@admin": return redirect(url_for("admin"))
    elif session.get("email"): return redirect(url_for("hortas"))
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
    hortas = db.hortas(session["email"])
    return jsonify(hortas)
    

@app.route("/remover/<chave>")
def remover(chave):
    db.remover_horta(chave)
    return redirect(url_for("hortas"))



#               #
#-----HORTA-----#
#               #



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
        "area": horta[2]})


@app.route("/consumo/<chave>")
def consumo(chave):
    return jsonify(calcular_consumo(chave))


@app.route("/historico/<chave>")
def historico(chave):
    return jsonify(db.historico(chave))



@app.route("/estacao")
def estacao():
    return jsonify(dados_meteorologicos())




#               #
#-----ESP32-----#
#               #


@app.route('/esp32/<chave>/volume')
def volume(chave):
    volumes = db.volumes(chave)
    if volumes:
        return jsonify({'volume': volumes[0],
                        'volume_irrigado': volumes[1],
                        "erro": "sem erro"}), 200
    return jsonify({'erro': 'Horta não encontrada'}), 404


@app.route('/esp32/<chave>/irrigado', methods=["POST"])
def volume_irrigado(chave):
    dados = request.json
    volume_irrigado = dados.get("volume_irrigado")
    db.adicionar_volume_irrigado(chave, volume_irrigado)

    return {"status": "Sucesso"}, 200















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

    
@app.route("/admin/adicionar_cultura", methods=["POST"])
def adicionar_cultura():
    nome = request.form["nome"]
    estagio = request.form["estagio"]
    duracao = request.form["duracao"]
    kc = request.form["kc"]
    
    db.adicionar_cultura(nome, estagio, duracao, kc)
    return redirect(url_for("culturas"))


@app.route("/admin/remover_cultura/<id>")
def remover_cultura(id):
    db.remover_cultura(id)
    return redirect(url_for("culturas"))
    

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
    return redirect(url_for("solos"))










app.run(debug=True, host="localhost", port=80)


#if __name__ == "__main__":
#    port = int(os.environ.get("PORT", 5000))
#    app.run(host="0.0.0.0", port=port)
