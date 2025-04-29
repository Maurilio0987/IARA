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
	 elemento_etc.innerHTML = " " + data["etc"];
	 elemento_volume.innerHTML = " " + data["volume"];
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

atualizar_consumo();
atualizar_estacao();

setInterval(atualizar_estacao, 900000);

