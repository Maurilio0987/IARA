from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
import os
#from banco_de_dados_pg import DatabaseManager, sha256
from db_supabase import DatabaseManager, sha256
import requests
import math
from pytz import timezone
import datetime


app = Flask(__name__)
app.secret_key = 'chave_secreta'  

url: str = "https://dphfvmjylwafuptvlqjz.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRwaGZ2bWp5bHdhZnVwdHZscWp6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI2OTk3MDMsImV4cCI6MjA2ODI3NTcwM30.A9GIqikHRUCjLVyFlyahOQVvWjD9Z_7gtwUELMAVxcg"  # encurtado para segurança
db = DatabaseManager(url, key)

#db_url = "postgresql://banco_de_dados_08i4_user:ac6u2uqkRDgkyBH9RUw3tbkiA3XXvb0h@dpg-d1lrl795pdvs73cbph0g-a.oregon-postgres.render.com/banco_de_dados_08i4"
#db = DatabaseManager(db_url)

dados_sensores = {}

DISTRIBUICAO_HORARIA_ETO = {
    0: 0.0,
    1: 0.0,
    2: 0.0,
    3: 0.0,
    4: 0.0,
    5: 0.0,
    6: 0.0,
    7: 0.01,
    8: 0.03,
    9: 0.05,
    10: 0.09,
    11: 0.13,
    12: 0.16,
    13: 0.16,
    14: 0.15,
    15: 0.11,
    16: 0.07,
    17: 0.04,
    18: 0.0,
    19: 0.0,
    20: 0.0,
    21: 0.0,
    22: 0.0,
    23: 0.0
}

#                 #
#-----FUNÇÕES-----#
#                 #

def calcular_consumo_diario(chave):
    horta = db.horta(chave)
    kc = horta[8]
    area = horta[2]

    sensores = dados_sensores.get(chave) # sensores de temperatura, umidade do solo e umidade do ar no dicionario
    try:
        if float(sensores["umidade_solo"]) > 70:
            return 0
    except:
        print("sem dados do sensor de umidade do solo")
        return 0
    
    response = requests.get("http://api.weatherapi.com/v1/forecast.json?key=c37bbfb8d14047ef8a231243253010&q=Apodi&days=1&aqi=no&alerts=no").json()
    tmax = response["forecast"]["forecastday"][0]["day"]["maxtemp_c"]
    tmin = response["forecast"]["forecastday"][0]["day"]["mintemp_c"]

    Ra = 35.4
    eto = kc * (0.0023 * Ra * ((tmax+tmin)/2 + 17.8) * ((tmax - tmin)**0.5))
    pendente = area * eto

    
    
    return round(pendente, 2)


def calcular_consumo_hora(chave):
    pendente = db.pendente_dia(chave)
    hora = datetime.datetime.now().hour
    print(pendente, hora)
    return pendente*DISTRIBUICAO_HORARIA_ETO[int(hora)] 


@app.route("/atualizar_hortas_diario")
def atualizar_hortas_rota():
    db.atualizar_hortas()
    chaves = db.chaves()
    for chave in chaves:            
        db.zerar_volumes(chave)
    
    return {"status": "success"}, 200


@app.route("/calcular_consumo_pendente_dia")
def calcular_consumo_pendente_dia_rota():
    chaves = db.chaves()
    for chave in chaves:
        db.adicionar_pendente_dia(chave, calcular_consumo_diario(chave))
    
    
    return {"status": "success"}, 200


@app.route("/calcular_consumo_pendente_hora")
def calcular_consumo_pendente_hora_rota():
    chaves = db.chaves()
    for chave in chaves:
        db.adicionar_pendente_hora(chave, calcular_consumo_hora(chave))
    
    
    return {"status": "success"}, 200


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
    flash("Email ou senha incorreto!")
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
        flash("Conta criada com sucesso!")
        return redirect(url_for("index"))
    flash("Erro ao criar conta")
    return redirect(url_for("cadastro"))









#                #   
#-----HORTAS-----#
#                #


@app.route("/hortas")
@login_required
def hortas():
    culturas = db.culturas()
    solos = db.solos()
    print(solos)
    print(culturas)
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



@app.route("/hortas/<chave>", methods=["GET"])
@login_required
def horta(chave):
    horta = db.horta(chave)
    return render_template("horta.html", horta={
        "nome": horta[1],
        "planta": horta[3],
        "solo": horta[4],
        "estagio": horta[6],
        "tempo": horta[7],
        "area": horta[2]}, chave=chave)


@app.route("/hortas/<chave>/dados", methods=["POST"])
def receber_dados(chave):
    sensores = request.json
    temperatura = sensores.get("temperatura")
    umidade_solo = sensores.get("umidade_solo")
    umidade_ar = sensores.get("umidade_ar")

    dados_sensores[chave] = {
        "temperatura": temperatura,
        "umidade_solo": umidade_solo,
        "umidade_ar": umidade_ar
    }

    return {"status": "success"}, 200




@app.route("/historico", methods=["GET", "POST"])
def historico():
    if request.method == "POST":
        dados = request.json
        horta = dados.get("horta")
        volume = dados.get("volume")

        if not horta or volume is None:
            return jsonify({"erro": "Campos 'horta' e 'volume' são obrigatórios"}), 400

        try:
            supabase.rpc("adicionar_ou_atualizar_historico", {
                "horta_param": horta,
                "volume_param": volume
            }).execute()

            return jsonify({"mensagem": "Histórico atualizado com sucesso"}), 200
        except Exception as e:
            return jsonify({"erro": str(e)}), 500

    elif request.method == "GET":
        horta_id = request.args.get("horta_id")
        dias = request.args.get("dias", default=7, type=int)
        print(horta_id)
        print(dias)
        if not horta_id:
            return jsonify({"erro": "horta_id é obrigatório"}), 400

        try:
            dados = db.historico_dias(horta_id, dias)
            return jsonify(dados)
        except Exception as e:
            return jsonify({"erro": str(e)}), 500



@app.route("/dados/<chave>", methods=["GET"])
def dados_rota(chave):
    dado = dados_sensores.get(chave)
    if dado: return dados_sensores[chave]
    else: return jsonify({"temperatura": "---",
                          "umidade_solo": "---",
                          "umidade_ar": "---"})



@app.route('/consumo/<chave>')
def consumo(chave):
    consumo = db.consumo(chave)
    if consumo:
        return jsonify({'pendente': consumo[0],
                        "irrigado": consumo[1],
                        "erro": "sem erro"}), 200
    return jsonify({'erro': 'Horta não encontrada'}), 404

@app.route('/esp32/consumo/<chave>')
def consumoesp(chave):
    consumo = db.consumo(chave)
    if consumo:
        return jsonify({'pendente': consumo[0] - consumo[1],
                        "erro": "sem erro"}), 200
    return jsonify({'erro': 'Horta não encontrada'}), 404

@app.route('/irrigado/<chave>', methods=["POST"])
def volume_irrigado(chave):
    dados = request.json
    irrigado = dados.get("irrigado")
    db.adicionar_consumo(chave, irrigado)

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

@app.route("/admin/remover_solo/<id>")
def remover_solo(id):
    db.remover_solo(id)
    return redirect(url_for("solos"))
    

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










if __name__ == "__main__":
    host = os.getenv("HOST", "192.168.3.41")
    port = os.getenv("PORT", 5678)
    debug = os.getenv("DEBUG", True)

    app.run(host=host, port=port, debug=debug)

