const BASE_URL = "https://10.180.0.100:8123/api/states/";
const TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI1MWFiZWY2ZTIyOWU0YjY5YTliNjc0NWU1MzhiZTI2NyIsImlhdCI6MTc0NTMyNTU3MywiZXhwIjoyMDYwNjg1NTczfQ.o07Qigaa-TOlNp1HFLBSzXYpMmVX0qOXZWl-WWASjKw";


const headers = {
  "Authorization": `Bearer ${TOKEN}`,
  "Content-Type": "application/json"
};

const sensorIds = {
  "sensor.vento_kmh": "Velocidade do Vento (km/h)",
  "sensor.direzione_vento": "Direção do Vento",
  "sensor.precipitacao_mm": "Precipitação (mm)",
  "sensor.tasmota_am2301_temperature": "Temperatura",
  "sensor.tasmota_am2301_humidity": "Umidade"
};



function atualizar_estacao() {
    fetch(BASE_URL, { headers })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Erro na requisição: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        let vento_kmh, direcao_vento, precipitacao_mm, temperatura, umidade;

        // Percorre os dados
        data.forEach(sensor => {
            switch (sensor.entity_id) {
                case "sensor.vento_kmh":
                    vento_kmh = sensor.state;
                    break;
                case "sensor.direzione_vento":
                    direcao_vento = sensor.state;
                    break;
                case "sensor.precipitacao_mm":
                    precipitacao_mm = sensor.state;
                    break;
                case "sensor.tasmota_am2301_temperature":
                    temperatura = sensor.state;
                    break;
                case "sensor.tasmota_am2301_humidity":
                    umidade = sensor.state;
                    break;
                }
        });

          // Exibe os valores
        console.log("Velocidade do Vento:", vento_kmh);
        console.log("Direção do Vento:", direcao_vento);
        console.log("Precipitação:", precipitacao_mm);
        console.log("Temperatura:", temperatura);
        console.log("Umidade:", umidade);


        let elemento_temperatura = document.getElementById("temperatura");
        let elemento_umidade = document.getElementById("umidade");

        elemento_temperatura.innerHTML = `${String(temperatura)}°C`;
        elemento_umidade.innerHTML = `${String(umidade)}%`;
        // Você pode usar essas variáveis onde quiser agora
        })
      .catch(error => {
        console.error("Erro ao obter dados:", error);
      });
}


function atualizar_tudo() {
	atualizar_estacao()
}


function umidade(valor) {
	fetch("/umidade", {
	method: "POST",
	headers: {"Content-Type": "application/json"},
	body: JSON.stringify({"umidade": valor})
	})
}

setInterval(atualizar_tudo, 2000);

