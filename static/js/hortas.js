function mostrarFormulario() {
   document.getElementById("hortaForm").style.display = "block";
   document.getElementById("overlay").style.display = "block";
}

function fecharFormulario() {
   document.getElementById("hortaForm").style.display = "none";
   document.getElementById("overlay").style.display = "none";
}
		
function atualizar_hortas() {
	fetch('/atualizar_hortas')
	.then(response => response.json()) // Converte a resposta para JSON
	.then(data => {
		let hortas_div = document.getElementById("hortasLista");
		hortas_div.innerHTML = "";
		
		for (let horta in data) {
			let horta_card = document.createElement("div");
			horta_card.className = "horta-card";
			horta_card.innerHTML = `<strong>Tamanho:</strong> ${data[horta][1]} m² <br>
									 <strong>Cultura:</strong> ${data[horta][2]} <br>
									 <strong>Solo:</strong> ${data[horta][3]}`;
												
			hortas_div.onclick = () => {window.location.href = `hortas/${data[horta][4]}`};
			hortas_div.appendChild(horta_card);
		}
	}) // Manipula os dados recebidos
	.catch(error => console.error('Erro:', error)); // Trata erros
	}
		
function cadastrarHorta() {
   let tamanho = document.getElementById("tamanho").value;
   let cultura = document.getElementById("cultura").value;
   let solo = document.getElementById("solo").value;
	let tempo = document.getElementById("tempo").value;
	let botao = document.getElementById("cadastrar");
			
   if (tamanho && cultura && solo) {
		botao.disabled = true;
				
      fetch('/cadastrar_horta', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({"tamanho": tamanho,
		   							 "cultura": cultura,
										 "solo": solo ,
										 "tempo": tempo })
         }).then(() => {
				fecharFormulario();
				atualizar_hortas()
				botao.disabled = false;
			});
   } else {
      alert("Preencha todos os campos!");
		botao.disabled = false;
	}
}
atualizar_hortas()