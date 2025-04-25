import requests
from time import sleep
"""

latitude = -5.6639
longitude = -37.7989

url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={latitude}&longitude={longitude}"
    f"&current=temperature_2m,relative_humidity_2m,cloud_cover,shortwave_radiation"
)

res = requests.get(url)

if res.status_code == 200:
    dados = res.json()["current"]
    print("🌤️ Dados atuais - Open-Meteo:")
    print(f"🌡️ Temperatura: {dados['temperature_2m']} °C")
    print(f"💧 Umidade: {dados['relative_humidity_2m']} %")
    print(f"☁️ Nebulosidade: {dados['cloud_cover']} %")
    print(f"☀️ Radiação solar: {dados['shortwave_radiation']} W/m²")
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