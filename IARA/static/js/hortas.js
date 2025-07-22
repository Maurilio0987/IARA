function mostrarFormulario() {
   document.getElementById("hortaForm").style.display = "block";
   document.getElementById("overlay").style.display = "block";
}


function fecharFormulario() {
   document.getElementById("hortaForm").style.display = "none";
   document.getElementById("overlay").style.display = "none";
}
		
function excluir(chave) {
	    // Remove qualquer modal anterior
    const modalExistente = document.getElementById('modal-excluir');
    if (modalExistente) {
        modalExistente.remove();
    }

    // Cria o modal
    const modal = document.createElement("div");
    modal.id = "modal-excluir";
    modal.className = "fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50";

    modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 shadow-lg w-full max-w-md">
            <h2 class="text-lg font-semibold mb-4 text-gray-800">Confirmar exclusão</h2>
            <p class="mb-6 text-gray-600">Tem certeza que deseja excluir esta horta?</p>
            <div class="flex justify-end gap-4">
					<button onclick="fecharModal()" class="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">Cancelar</button>                
					<button onclick="window.location.href='remover/${chave}'" class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">Excluir</button>
            </div>
         </div>
    `;
    document.body.appendChild(modal);
}

function fecharModal() {
    const modal = document.getElementById("modal-excluir");
    if (modal) {
        modal.remove();
    }
}

function atualizar_hortas() {
	fetch('/atualizar_hortas')
	.then(response => response.json()) // Converte a resposta para JSON
	.then(data => {
		let hortas_div = document.getElementById("hortasLista");
		hortas_div.innerHTML = "";
		
		console.log(data);
		for (let horta in data) {
			let horta_card = document.createElement("div");
			horta_card.className = "horta-card";
			horta_card.innerHTML = `<div class="bg-white rounded-lg card p-6 hover:shadow-md"><div class="flex justify-between items-start mb-4"><h3 class="text-xl font-semibold text-emerald-800">${data[horta][1]}</h3><div class="flex space-x-2"><button class="text-emerald-600 hover:text-emerald-800"><i class="fas fa-edit"></i></button><button onclick="excluir('${data[horta][2]}')" class="text-red-500 hover:text-red-700"><i class="fas fa-trash"></i></button></div></div><div class="space-y-2 text-gray-700"><p><span class="font-medium">Tamanho:</span> ${data[horta][3]}</p><p><span class="font-medium">Cultura:</span> ${data[horta][4]}</p><p><span class="font-medium">Solo:</span> ${data[horta][5]}</p></div><div class="mt-4 pt-4 border-t border-gray-200"><a id="ver" onclick="window.location.href='hortas/${data[horta][2]}'" class="text-emerald-600 cursor-pointer hover:text-emerald-800 font-medium flex items-center">Ver detalhes <i class="fas fa-arrow-right ml-2"></i></a></div></div>`;
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
