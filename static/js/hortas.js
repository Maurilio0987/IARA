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
			horta_card.innerHTML = `<div class="bg-white rounded-lg card p-6 cursor-pointer hover:shadow-md"><div class="flex justify-between items-start mb-4"><h3 class="text-xl font-semibold text-emerald-800">${data[horta][1]}</h3><div class="flex space-x-2"><button class="text-emerald-600 hover:text-emerald-800"><i class="fas fa-edit"></i></button><button class="text-red-500 hover:text-red-700"><i class="fas fa-trash"></i></button></div></div><div class="space-y-2 text-gray-700"><!---<p><span class="font-medium">Tamanho:</span> 3 m²</p><p><span class="font-medium">Cultura:</span> Coentro</p><p><span class="font-medium">Solo:</span> Arenoso</p>--></div><div class="mt-4 pt-4 border-t border-gray-200"><a href="#" class="text-emerald-600 hover:text-emerald-800 font-medium flex items-center">Ver detalhes <i class="fas fa-arrow-right ml-2"></i></a></div></div>`;
			hortas_div.onclick = () => {window.location.href = `hortas/${data[horta][2]}`};
			hortas_div.appendChild(horta_card);
		}
	}) // Manipula os dados recebidos
	.catch(error => console.error('Erro:', error)); // Trata erros
	}
		
		
function cadastrarHorta() {
   let nome = document.getElementById("nome").value
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
         body: JSON.stringify({"nome": nome,
										 "tamanho": tamanho,
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