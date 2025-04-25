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

atualizar_estacao();

setInterval(atualizar_estacao, 5000);

