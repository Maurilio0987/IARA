function atualizar_estacao() {
   fetch('/estacao')
  .then(response => {
    if (!response.ok) {
      throw new Error(`Erro na requisição: ${response.status}`);
    }
    return response.json(); // ou response.text() se for texto
  })
  .then(data => {
    
	 let elemento_temperatura = document.getElementById("temperatura");
	 let elemento_umidade = document.getElementById("umidade");
	 let elemento_solar = document.getElementById("solar");
	 
	 elemento_temperatura.innerHTML = " " + data["temperatura"]
	 elemento_umidade.innerHTML = " " + data["umidade"]
	 elemento_solar.innerHTML = " " + data["radiacao_solar"]
	 
	 
  })
  .catch(error => {
    console.error('Erro ao buscar os dados:', error);
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

setInterval(atualizar_tudo, 900000);

