function getChaveHorta() {
  const partes = window.location.pathname.split('/');
  return partes[partes.length - 1];
}

function atualizar_consumo() {
  const chave = getChaveHorta();
  fetch("/consumo/"+chave)
  .then(response => {
    if (!response.ok) {
      throw new Error(`Erro na requisição: ${response.status}`);
    }
    return response.json(); // ou response.text() se for texto
  })
  .then(data => {
     console.log(data);
	 let elemento_eto = document.getElementById("eto");
	 let elemento_etc = document.getElementById("etc");
	 let elemento_volume = document.getElementById("volume");


	 elemento_eto.innerHTML = " " + data["eto"];
	 //elemento_etc.innerHTML = " " + data["etc"];
	 //elemento_volume.innerHTML = " " + data["consumo"];
	})

  .catch(error => {
    console.error('Erro ao buscar os dados:', error);
  });
}

function atualizar_historico() {
  const chave = getChaveHorta();
  fetch("/historico/"+chave)
  .then(response => {
    if (!response.ok) {
      throw new Error(`Erro na requisição: ${response.status}`);
    }
    return response.json(); // ou response.text() se for texto
  })
  .then(data => {
	const diasSemana = ['Há 6 dias', 'Há 5 dias', 'Há 4 dias', 'Há 3 dias', 'Há 2 dias', 'Ontem', 'Hoje'];
	data[0] = JSON.parse(data[0]);
	const consumo = [data[0][0], data[0][1], data[0][2], data[0][3], data[0][4], data[0][5], data[1]];
	gerarGraficoConsumo(diasSemana, consumo);

	})

  .catch(error => {
    console.error('Erro ao buscar os dados:', error);
  });
}

function gerarGraficoConsumo(dias, valores) {
   const ctx = document.getElementById('graficoAgua').getContext('2d');
   new Chart(ctx, {
      type: 'line',
      data: {
				labels: dias,
				datasets: [{
					label: 'Consumo de água (L/dia)',
					data: valores,
					borderColor: '#2c50af',
					backgroundColor: 'rgba(36, 80, 175, 0.2)',
					fill: true,
					tension: 0.3
    			}]
      },
      options: {
			responsive: true,
         maintainAspectRatio: false,
			plugins: {
				legend: {
					display: true
				},
				tooltip: {
					enabled: true
				}
			},
			scales: {
				y: {
					beginAtZero: true,
					title: {
					display: true,
					text: 'Litros'
					}
            },
				x: {
					title: {
						display: true,
						text: 'Dias da semana'
				   }
				}
			}
      }
   });
}
		
		  
function atualizar_consumo24() {
  const chave = getChaveHorta();
  fetch("/esp32/"+chave+"/volume")
  .then(response => {
    if (!response.ok) {
      throw new Error(`Erro na requisição: ${response.status}`);
    }
    return response.json(); // ou response.text() se for texto
  })
  .then(data => {
     console.log(data);
	 let elemento_eto = document.getElementById("volume_irrigado");
	 

	 
	 elemento_eto.innerHTML = " " + data["volume_irrigado"];
	 animateVolume(document.getElementById("volume_irrigado"), data["volume_irrigado"]);

	})
	
  .catch(error => {
    console.error('Erro ao buscar os dados:', error);
  });
}


function atualizar_estacao() {
   fetch('/estacao')
  .then(response => {
    if (!response.ok) {
      throw new Error(`Erro na requisição: ${response.status}`);
    }
    return response.json(); // ou response.text() se for texto
  })
  .then(data => {
     console.log(data);
	 let elemento_temperatura = document.getElementById("temperatura");
	 let elemento_umidade = document.getElementById("umidade");
	 let elemento_solar = document.getElementById("radiacao");
	 let elemento_vento = document.getElementById("vento");
	 
	 elemento_temperatura.innerHTML = " " + data["temperatura"];
	 elemento_umidade.innerHTML = " " + data["umidade"];
	 elemento_solar.innerHTML = " " + data["radiacao_solar"];
	 elemento_vento.innerHTML = " " + data["vento"];
	})
  
  .catch(error => {
    console.error('Erro ao buscar os dados:', error);
  });
}

function animateVolume(element, finalValue) {
	const span = element;
	let current = 0;
	const duration = 1500;
	const increment = finalValue / (duration / 30);

	const interval = setInterval(() => {
		current += increment;
		if (current >= finalValue) {
			current = finalValue;
			clearInterval(interval);
		}
		span.textContent = current.toFixed(1);
	}, 30);
}

		
atualizar_consumo();
atualizar_estacao();
atualizar_historico();
atualizar_consumo24();

setInterval(atualizar_estacao, 900000);

