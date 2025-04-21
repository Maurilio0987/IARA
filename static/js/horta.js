var API_ESTACAO = "";



function atualizar_estacao() {
	fetch("API_ESTACAO")
	.then(response => {
		return response.json(); 
	})
	.then(data => {
		let elemento_temperatura = document.getElementById("temperatura");
		let elemento_umidade = document.getElementById("umidade");
		let valor_temperatura = data["temperatura"];
		let valor_umidade = data["umidade"];
		
		elemento_temperatura.innerHTML = `${String(valor_temperatura)}%`;
		elemento_umidade.innerHTML = `${String(valor_umidade)}%`;
	})
	.catch(error => {
      console.error('Erro:', error);
   });
}


function atualizar_tudo() {
	atualizar_umidade()
}


function umidade(valor) {
	fetch("/umidade", {
	method: "POST",
	headers: {"Content-Type": "application/json"},
	body: JSON.stringify({"umidade": valor})
	})
}

//setInterval(atualizar_tudo, 2000);

