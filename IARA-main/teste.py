from time import sleep
import math
import requests
import requests
import math
import time


def calcular_eto(temperatura, umidade, rad_solar, velocidade_vento):
	# Constantes para o método Penman-Monteith
	T = temperatura  # Temperatura média (°C)
	RH = umidade  # Umidade relativa (%)
	Rn = rad_solar  # Radiação solar (W/m²)
	u2 = velocidade_vento  # Velocidade do vento a 2m (m/s)

	# Conversão da radiação solar de W/m² para MJ/m²/dia (1 W/m² = 0.0864 MJ/m²/h)
	Rn = Rn * 0.0864 * 24  # MJ/m²/dia

	# Pressão de saturação do vapor (es) (kPa)
	es = 0.6108 * math.exp((17.27 * T) / (T + 237.3))

	# Pressão de vapor atual (ea) (kPa)
	ea = (RH / 100) * es

	# Declive da curva de saturação do vapor (Δ) (kPa/°C)
	delta = (4098 * es) / ((T + 237.3) ** 2)

	# Constante psicrométrica (γ) (kPa/°C)
	gamma = 0.066  # Valor típico para condições médias de pressão atmosférica e altitude

	# Cálculo do ETo (mm/dia) utilizando a fórmula Penman-Monteith
	ETo = (0.408 * delta * (Rn) + gamma * (900 / (T + 273)) * u2 * (es - ea)) / (delta + gamma * (1 + 0.34 * u2))

	return ETo


def obter_dados_estacao():
	latitude = -5.6622
	longitude = -37.7989

	url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,shortwave_radiation,wind_speed_10m"

	res = requests.get(url)
	if res.status_code == 200:
		dados = res.json()["current"]
		temperatura = dados['temperature_2m']
		umidade = dados['relative_humidity_2m']
		rad_solar = dados['shortwave_radiation']
		velocidade_vento = dados['wind_speed_10m']  # Velocidade do vento a 10 metros

		# Convertendo a velocidade do vento para a altura de 2 metros
		velocidade_vento_2m = velocidade_vento * (4.87 / math.log(67.8 * 10 - 5.42))

		return temperatura, umidade, rad_solar, velocidade_vento_2m
	else:
		print("Erro ao buscar dados:", res.status_code)
		return None

temperatura, umidade, rad_solar, velocidade_vento_2m = obter_dados_estacao()
print(calcular_eto(temperatura, umidade, rad_solar, velocidade_vento_2m))
"""
# Coordenadas de Apodi, RN
latitude = -5.6578
longitude = -37.8000

# URL da API Open-Meteo
url = "https://api.open-meteo.com/v1/forecast"

# Parâmetros da requisição
params = {
    "latitude": latitude,
    "longitude": longitude,
    "daily": "et0_fao_evapotranspiration",
    "timezone": "America/Fortaleza"
}

# Realizando a requisição
response = requests.get(url, params=params)

# Verificando o status da requisição
if response.status_code == 200:
    dados = response.json()
    print("Previsão de ETo para Apodi, RN:")
    for dia in dados["daily"]["time"]:
        print(f"{dia}: {dados['daily']['et0_fao_evapotranspiration'][dados['daily']['time'].index(dia)]} mm/dia")
else:
    print(f"Erro ao obter dados: {response.status_code}")

"""
"""
def calcular_eto(temperatura, umidade, rad_solar, velocidade_vento):
    # Constantes para o método Penman-Monteith
    T = temperatura  # Temperatura média (°C)
    RH = umidade  # Umidade relativa (%)
    Rn = rad_solar  # Radiação solar (W/m²)
    u2 = velocidade_vento  # Velocidade do vento a 2m (m/s)

    # Conversão da radiação solar de W/m² para MJ/m²/dia (1 W/m² = 0.0864 MJ/m²/h)
    Rn = Rn * 0.0864 * 24  # MJ/m²/dia

    # Pressão de saturação do vapor (es) (kPa)
    es = 0.6108 * math.exp((17.27 * T) / (T + 237.3))

    # Pressão de vapor atual (ea) (kPa)
    ea = (RH / 100) * es

    # Declive da curva de saturação do vapor (Δ) (kPa/°C)
    delta = (4098 * es) / ((T + 237.3) ** 2)

    # Constante psicrométrica (γ) (kPa/°C)
    gamma = 0.066  # Valor típico para condições médias de pressão atmosférica e altitude

    # Cálculo do ETo (mm/dia) utilizando a fórmula Penman-Monteith
    ETo = (0.408 * delta * (Rn) + gamma * (900 / (T + 273)) * u2 * (es - ea)) / (delta + gamma * (1 + 0.34 * u2))

    return ETo

while True:
    # Latitude e longitude
    latitude = -5.6639
    longitude = -37.7989

    # Requisição para pegar os dados meteorológicos
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,shortwave_radiation,wind_speed_10m"
    )

    res = requests.get(url)

    if res.status_code == 200:
        dados = res.json()["current"]
        temperatura = dados['temperature_2m']
        umidade = dados['relative_humidity_2m']
        rad_solar = dados['shortwave_radiation']
        velocidade_vento = dados['wind_speed_10m']  # Velocidade do vento a 10 metros

        # Convertendo a velocidade do vento para a altura de 2 metros
        velocidade_vento_2m = velocidade_vento * (4.87 / math.log(67.8 * 10 - 5.42))

        print("🌤️ Dados atuais - Open-Meteo:")
        print(f"🌡️ Temperatura: {temperatura} °C")
        print(f"💧 Umidade: {umidade} %")
        print(f"☀️ Radiação solar: {rad_solar} W/m²")
        print(f"🌬️ Velocidade do vento (2m): {velocidade_vento_2m:.2f} m/s")

        # Calcular o ETo
        eto = calcular_eto(temperatura, umidade, rad_solar, velocidade_vento_2m)
        print(f"💧 ETo: {eto:.2f} mm/dia")
    else:
        print("Erro ao buscar dados:", res.status_code)
"""
"""
# Configurações
home_assistant_url = 'http://10.180.0.100:8123'
access_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI1MWFiZWY2ZTIyOWU0YjY5YTliNjc0NWU1MzhiZTI2NyIsImlhdCI6MTc0NTMyNTU3MywiZXhwIjoyMDYwNjg1NTczfQ.o07Qigaa-TOlNp1HFLBSzXYpMmVX0qOXZWl-WWASjKw'
entity_id = 'sensor.temperatura_sala'

# Cabeçalhos para autenticação
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
}

# Endpoint da API para o estado de uma entidade
url = f'{home_assistant_url}/api/states'

# Requisição GET
response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    print(data)
    #print(f"Estado atual de {entity_id}: {data['state']}")
    #print("Atributos:", data['attributes'])
else:
    print("Erro ao acessar a API:", response.status_code, response.text)
"""
"""
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
while True:
    try:
        response = requests.get(BASE_URL, headers=headers)
        response.raise_for_status()

        dados = response.json()
        resultado = {}

        for sensor in dados:
            eid = sensor.get("entity_id")
            if eid in sensor_ids:
                resultado[sensor_ids[eid]] = sensor.get("state")
        resposta = {"precipitacao": resultado["precipitacao"],
                    "vento": resultado["velocidade_vento"],
                    "direcao": resultado["direcao_vento"],
                    "temperatura": resultado["temperatura"],
                    "umidade": resultado["umidade"]}
        print(resultado)

    except requests.exceptions.RequestException as e:
        print("Erro ao conectar com o Home Assistant:", e)
        print({"precipitacao": "---",
                "vento": "---",
                "direcao": "---",
                "temperatura": "---",
                "umidade": "---"})
    sleep(2/10)
"""