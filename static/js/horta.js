let graficoConsumo = null;
let ultimoConsumo = null;
let ultimoPendente = null;

function getChaveHorta() {
  const partes = window.location.pathname.split('/');
  return partes[partes.length - 1];
}


function atualizar_historico() {
  const chave = getChaveHorta();
  const dias = 7;

  fetch(`/historico?horta_id=${chave}&dias=${dias}`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`Erro na requisição: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      const diasSemana = ['Há 6 dias', 'Há 5 dias', 'Há 4 dias', 'Há 3 dias', 'Há 2 dias', 'Ontem', 'Hoje'];
      const consumo = data.map(item => item[1]);
      
      gerarGraficoConsumo(diasSemana, consumo);
    })
    .catch(error => {
      console.error('Erro ao buscar os dados:', error);
    });
}



function gerarGraficoConsumo(dias, valores) {
   const ctx = document.getElementById('graficoAgua').getContext('2d');

   // Destruir gráfico antigo, se existir
   if (graficoConsumo) {
       graficoConsumo.destroy();
   }

   graficoConsumo = new Chart(ctx, {
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
    //console.log(data);
     if (ultimoPendente != data["pendente"] || ultimoConsumo != data["irrigado"]) {
     	ultimoConsumo = data["irrigado"];
     	// ultimoPendente = data["pendente"]
     	atualizar_historico()
	     	
		let elemento_irrigado = document.getElementById("volume_irrigado");
	 	// let elemento_pendente = document.getElementById("volume");

	  // elemento_pendente.innerHTML = data["pendente"];
	 	elemento_irrigado.innerHTML = data["irrigado"];
     }
	})
	
  .catch(error => {
    console.error('Erro ao buscar os dados:', error);
  });
}

setInterval(atualizar_consumo, 3000);

