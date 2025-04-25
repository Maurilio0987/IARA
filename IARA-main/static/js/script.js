function atualizar_umidade() {
	fetch("/dados")
	.then(response => {
		return response.json(); 
	})
	.then(data => {
		let barra_umidade = document.getElementById("barra_de_umidade");
		let umidade = document.getElementById("umidade");
		let valor_umidade = data["umidade"];
		
		barra_umidade.style["width"] = `${String(valor_umidade)}%`;
		umidade.innerHTML = `${String(valor_umidade)}%`;
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

setInterval(atualizar_tudo, 2000);

