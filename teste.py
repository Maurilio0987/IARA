"""import requests

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

import requests

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
