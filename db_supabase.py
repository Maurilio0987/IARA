from supabase import create_client, Client
import hashlib
from datetime import datetime, timedelta, date, timezone
import pytz

url: str = "https://dphfvmjylwafuptvlqjz.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRwaGZ2bWp5bHdhZnVwdHZscWp6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI2OTk3MDMsImV4cCI6MjA2ODI3NTcwM30.A9GIqikHRUCjLVyFlyahOQVvWjD9Z_7gtwUELMAVxcg"  # encurtado para segurança


def sha256(texto):
    sha = hashlib.sha256()
    sha.update(texto.encode('utf-8'))
    return sha.hexdigest()


class DatabaseManager:
    def __init__(self, url, key):
        self.supabase: Client = create_client(url, key)

    def verificar_email(self, email):
        resposta = self.supabase.table("usuarios").select("id").eq("email", email).execute()
        return len(resposta.data) > 0

    def verificar_senha(self, email, senha):
        resposta = self.supabase.table("usuarios").select("senha_hash").eq("email", email).limit(1).execute()

        if resposta.data:
            senha_hash = resposta.data[0]["senha_hash"]
            return senha_hash == senha
        else:
            return False

    def adicionar_usuario(self, email, senha):
        dados = {
            "email": email,
            "senha_hash": senha
        }
        resposta = self.supabase.table("usuarios").insert(dados).execute()
        return resposta.data

    def usuario(self, email):
        resposta = self.supabase.table("usuarios").select("id").eq("email", email).limit(1).execute()

        if resposta.data:
            return resposta.data[0]["id"]
        else:
            return None

    def hortas(self, email):
        # Passo 1: Buscar id do usuário
        user_resp = self.supabase.table("usuarios").select("id").eq("email", email).limit(1).execute()
        if not user_resp.data:
            return []

        usuario_id = user_resp.data[0]["id"]

        # Passo 2: Buscar hortas desse usuário
        hortas_resp = self.supabase.table("hortas").select("*").eq("usuario_id", usuario_id).execute()
        hortas_raw = hortas_resp.data

        hortas_final = []

        for horta in hortas_raw:
            # Passo 3.1: Buscar solo
            solo_resp = self.supabase.table("solos").select("nome").eq("id", horta["solo_id"]).limit(1).execute()
            solo_nome = solo_resp.data[0]["nome"] if solo_resp.data else "Desconhecido"

            # Passo 3.2: Buscar estágio
            estagio_resp = self.supabase.table("estagios").select("cultura_id").eq("id", horta["estagio_id"]).limit(1).execute()
            cultura_id = estagio_resp.data[0]["cultura_id"] if estagio_resp.data else None

            # Passo 3.3: Buscar cultura
            if cultura_id:
                cultura_resp = self.supabase.table("culturas").select("nome").eq("id", cultura_id).limit(1).execute()
                cultura_nome = cultura_resp.data[0]["nome"] if cultura_resp.data else "Desconhecido"
            else:
                cultura_nome = "Desconhecido"

            # Adiciona horta com dados combinados
            hortas_final.append([
                horta["id"],
                horta["nome"],
                horta["chave"],
                horta["tamanho"],
                cultura_nome,
                solo_nome])

        return hortas_final


    def horta(self, chave):
        # 1. Buscar a horta pela chave
        resp = self.supabase.table("hortas").select("*").eq("chave", chave).limit(1).execute()
        if not resp.data:
            return None

        horta = resp.data[0]

        # 2. Buscar solo
        solo_resp = self.supabase.table("solos").select("nome").eq("id", horta["solo_id"]).limit(1).execute()
        solo_nome = solo_resp.data[0]["nome"] if solo_resp.data else "Desconhecido"

        # 3. Buscar estágio
        estagio_resp = self.supabase.table("estagios").select("nome", "kc", "cultura_id").eq("id", horta["estagio_id"]).limit(1).execute()
        if estagio_resp.data:
            estagio_nome = estagio_resp.data[0]["nome"]
            kc = estagio_resp.data[0]["kc"]
            cultura_id = estagio_resp.data[0]["cultura_id"]
        else:
            estagio_nome = "Desconhecido"
            kc = None
            cultura_id = None

        # 4. Buscar cultura
        if cultura_id:
            cultura_resp = self.supabase.table("culturas").select("nome").eq("id", cultura_id).limit(1).execute()
            cultura_nome = cultura_resp.data[0]["nome"] if cultura_resp.data else "Desconhecido"
        else:
            cultura_nome = "Desconhecido"

        # 5. Montar resultado
        return [
            horta["id"],
            horta["nome"],
            horta["tamanho"],
            cultura_nome,
            solo_nome,
            horta["chave"],
            estagio_nome,
            horta["duracao"],
            kc
        ]


    def adicionar_horta(self, usuario_id, nome, tamanho, cultura_id, solo_id, tempo):
        estagio_id = self.estagio(cultura_id, tempo)
        if estagio_id is not None:

            data = {
                "usuario_id": usuario_id,
                "nome": nome,
                "tamanho": tamanho,
                "duracao": tempo,
                "solo_id": solo_id,
                "estagio_id": estagio_id
            }

            resp = self.supabase.table("hortas").insert(data).execute()

            return bool(resp.data)  # True se inseriu com sucesso
        return False


    def adicionar_solo(self, nome, capacidade_campo, ponto_murcha, densidade, porosidade, cond_hidraulica):
        data = {
            "nome": nome,
            "capacidade_campo": capacidade_campo,
            "ponto_murcha": ponto_murcha,
            "densidade": densidade,
            "porosidade": porosidade,
            "cond_hidraulica": cond_hidraulica
        }

        self.supabase.table("solos").insert(data).execute()


    def adicionar_cultura(self, nome, estagio, duracao, kc):
        nome = nome.capitalize()
        estagio = estagio.capitalize()

        # Verifica se a cultura já existe
        cultura_resp = self.supabase.table("culturas").select("id").eq("nome", nome).execute()
        cultura_dados = cultura_resp.data

        if cultura_dados:
            cultura_id = cultura_dados[0]["id"]
        else:
            insert_resp = self.supabase.table("culturas").insert({"nome": nome}).execute()
            cultura_id = insert_resp.data[0]["id"]

        # Pega o último número de estágio dessa cultura
        estagio_resp = self.supabase.table("estagios").select("numero_estagio").eq("cultura_id", cultura_id).order("numero_estagio", desc=True).limit(1).execute()
        dados_estagio = estagio_resp.data

        proximo_numero = (dados_estagio[0]["numero_estagio"] if dados_estagio else 0) + 1

        # Insere o novo estágio
        self.supabase.table("estagios").insert({
            "cultura_id": cultura_id,
            "numero_estagio": proximo_numero,
            "nome": estagio,
            "duracao": duracao,
            "kc": kc
        }).execute()


    def adicionar_pendente_dia(self, chave, litros):
        resp = self.supabase.table("hortas") \
            .select("id, pendente_dia") \
            .eq("chave", chave) \
            .limit(1) \
            .execute()

        if resp.data:
            registro = resp.data[0]
            pendente_atual = registro.get("pendente_dia", 0) or 0  # evita erro se pendente for None
            novo_pendente = pendente_atual + litros

            # Atualiza o valor de pendente
            self.supabase.table("hortas") \
                .update({"pendente_dia": novo_pendente}) \
                .eq("id", registro["id"]) \
                .execute()
        else:
            print(f"[ERRO] Nenhuma horta encontrada com chave '{chave}'")

    def adicionar_pendente_hora(self, chave, litros):
        resp = self.supabase.table("hortas") \
            .select("id, pendente_hora") \
            .eq("chave", chave) \
            .limit(1) \
            .execute()

        if resp.data:
            registro = resp.data[0]
            pendente_atual = registro.get("pendente_hora", 0) or 0  # evita erro se pendente for None
            novo_pendente = pendente_atual + litros

            # Atualiza o valor de pendente
            self.supabase.table("hortas") \
                .update({"pendente_hora": novo_pendente}) \
                .eq("id", registro["id"]) \
                .execute()
        else:
            print(f"[ERRO] Nenhuma horta encontrada com chave '{chave}'")

    def pendente_dia(self, chave):
        try:
            # Busca apenas a coluna "pendente"
            resp = self.supabase.table("hortas") \
                .select("pendente_dia") \
                .eq("chave", chave) \
                .limit(1) \
                .execute()

            if resp.data:
                registro = resp.data[0]
                
                # Pega o valor, garantindo que 0.0 seja o padrão se for None ou não existir
                pendente_atual = registro.get("pendente_dia", 0.0) or 0.0
                
                return float(pendente_atual) # Garante que o retorno seja um float
            else:
                # Imprime o mesmo erro da sua outra função
                print(f"[ERRO] Nenhuma horta encontrada com chave '{chave}'")
                return 0.0

        except Exception as e:
            print(f"[ERRO] Falha ao consultar Supabase: {e}")
            return 0.0

    def pendente_hora(self, chave):
        try:
            # Busca apenas a coluna "pendente"
            resp = self.supabase.table("hortas") \
                .select("pendente_hora") \
                .eq("chave", chave) \
                .limit(1) \
                .execute()

            if resp.data:
                registro = resp.data[0]
                
                # Pega o valor, garantindo que 0.0 seja o padrão se for None ou não existir
                pendente_atual = registro.get("pendente_hora", 0.0) or 0.0
                
                return float(pendente_atual) # Garante que o retorno seja um float
            else:
                # Imprime o mesmo erro da sua outra função
                print(f"[ERRO] Nenhuma horta encontrada com chave '{chave}'")
                return 0.0

        except Exception as e:
            print(f"[ERRO] Falha ao consultar Supabase: {e}")
            return 0.0

    def adicionar_consumo(self, chave, litros):
        hoje = date.today().isoformat()

        # Tenta buscar o registro de hoje para a horta
        resp = self.supabase.table("historico") \
            .select("id, consumo") \
            .eq("horta", chave) \
            .eq("data", hoje) \
            .limit(1) \
            .execute()

        if resp.data:
            # Já existe um registro para hoje, atualiza o consumo
            registro = resp.data[0]
            novo_consumo = registro["consumo"] + litros

            self.supabase.table("historico") \
                .update({"consumo": novo_consumo}) \
                .eq("id", registro["id"]) \
                .execute()
        else:
            # Não existe registro para hoje, cria um novo
            self.supabase.table("historico").insert({
                "horta": chave,
                "data": hoje,
                "consumo": litros
            }).execute()


    def atualizar_hortas(self):
        hortas = self.supabase.table("hortas").select("*").execute().data

        for horta in hortas:
            nova_duracao = horta["duracao"] + 1
            estagio_atual_id = horta["estagio_id"]

            cultura_id_resp = self.supabase.table("estagios").select("cultura_id").eq("id", estagio_atual_id).limit(1).execute()
            if not cultura_id_resp.data:
                continue

            cultura_id = cultura_id_resp.data[0]["cultura_id"]
            novo_estagio_id = self.estagio(cultura_id, nova_duracao)

            update_data = {"duracao": nova_duracao}
            if novo_estagio_id and novo_estagio_id != estagio_atual_id:
                update_data["estagio_id"] = novo_estagio_id

            self.supabase.table("hortas").update(update_data).eq("id", horta["id"]).execute()


    def remover_horta(self, chave):
        self.supabase.table("hortas").delete().eq("chave", chave).execute()


    def remover_cultura(self, estagio_id):
        estagio_resp = self.supabase.table("estagios").select("cultura_id").eq("id", estagio_id).limit(1).execute()
        if not estagio_resp.data:
            raise ValueError("Estágio não encontrado.")

        cultura_id = estagio_resp.data[0]["cultura_id"]
        self.supabase.table("estagios").delete().eq("id", estagio_id).execute()

        estagios_restantes = self.supabase.table("estagios").select("id").eq("cultura_id", cultura_id).order("numero_estagio").execute().data

        if not estagios_restantes:
            self.supabase.table("culturas").delete().eq("id", cultura_id).execute()
        else:
            for i, est in enumerate(estagios_restantes, start=1):
                self.supabase.table("estagios").update({"numero_estagio": i}).eq("id", est["id"]).execute()


    def remover_solo(self, id):
        resposta = self.supabase.table("solos").delete().eq("id", id).execute()


    def historico_dias(self, horta_id, dias):
        """
        Retorna os últimos 'dias' de registros da tabela historico para a horta específica.
        Dias sem registros terão volume 0.
        :param horta_id: UUID da horta (chave estrangeira).
        :param dias: Quantidade de dias anteriores a incluir (ex: 7 para últimos 7 dias).
        :return: Lista de listas no formato [[data_str, volume], ...]
        """
        tz_fortaleza = pytz.timezone("America/Fortaleza")
        hoje = hoje = datetime.now(tz_fortaleza).date()
        data_limite = (hoje - timedelta(days=dias - 1)).isoformat()

        # Consulta ao Supabase
        resposta = self.supabase.table("historico") \
            .select("data, consumo") \
            .eq("horta", horta_id) \
            .gte("data", data_limite) \
            .order("data", desc=False) \
            .execute()

        registros = {r['data']: r['consumo'] for r in resposta.data} if resposta.data else {}
      
        resultado = []
        for i in range(dias):
            dia = (hoje - timedelta(days=dias - 1 - i)).isoformat()
            consumo = registros.get(dia, 0)
            resultado.append([dia, consumo])
      
        return resultado

  
    def culturas(self):
        culturas = self.supabase.table("culturas").select("id,nome").execute().data
        resultado = {}
        for cultura in culturas:
            nome = cultura["nome"]
            if nome not in resultado or cultura["id"] < resultado[nome]["id"]:
                resultado[nome] = cultura
        # Retornar apenas os valores como lista de listas
        return [[c["id"], c["nome"]] for c in resultado.values()]


    def solos(self):
        solos = self.supabase.table("solos").select("id, nome").execute().data
        return [[solo["id"], solo["nome"]] for solo in solos]


    def estagio(self, cultura_id, tempo):
        estagios = self.supabase.table("estagios").select("id, duracao").eq("cultura_id", cultura_id).order("numero_estagio").execute().data

        tempo_acumulado = 0
        for estagio in estagios:
            tempo_acumulado += estagio["duracao"]
            if tempo <= tempo_acumulado:
                return estagio["id"]
        return estagios[-1]["id"] if estagios else None


    def chaves(self):
        resp = self.supabase.table("hortas").select("chave").execute()
        return [x["chave"] for x in resp.data]


    def consumo(self, chave):
        # Primeiro: buscar o valor de "pendente" da tabela "hortas"
        resp_horta = self.supabase.table("hortas").select("chave, pendente_hora").eq("chave", chave).limit(1).execute()
        if not resp_horta.data:
            return (None, None)
        print(resp_horta)
        horta_chave = resp_horta.data[0]["chave"]
        pendente = resp_horta.data[0]["pendente_hora"]

        # Segundo: buscar o valor de "consumo" do dia atual da tabela "historico"
        hoje = str(date.today())  # formato: 'YYYY-MM-DD'
        resp_consumo = self.supabase.table("historico").select("consumo").eq("horta", horta_chave).eq("data", hoje).limit(1).execute()
        
        consumo = resp_consumo.data[0]["consumo"] if resp_consumo.data else 0

        return [float(pendente), float(consumo)]


    def zerar_volumes(self, chave):
        # Atualiza o campo 'pendente' para 0 na tabela 'hortas' para a horta com a chave fornecida
        self.supabase.table("hortas") \
            .update({"pendente_dia": 0, "pendente_hora": 0}) \
            .eq("chave", chave) \
            .execute()





    def tabela(self, nome_tabela):
        if nome_tabela == "culturas":
            culturas_resp = self.supabase.table("culturas").select("id", "nome").execute()
            estagios_resp = self.supabase.table("estagios").select("id", "cultura_id", "nome", "duracao", "kc", "numero_estagio").execute()

            if not culturas_resp.data or not estagios_resp.data:
                return []

            culturas = culturas_resp.data
            estagios = estagios_resp.data

            # Agrupar estágios por cultura_id
            from collections import defaultdict
            estagios_por_cultura = defaultdict(list)
            for e in estagios:
                estagios_por_cultura[e["cultura_id"]].append(e)

            linhas = []
            for cultura in sorted(culturas, key=lambda x: x["nome"]):
                c_id = cultura["id"]
                c_nome = cultura["nome"]
                ests = sorted(estagios_por_cultura[c_id], key=lambda x: x["numero_estagio"])
                qtd_estagios = len(ests)
                for est in ests:
                    linhas.append([
                        c_nome,
                        est["nome"],
                        est["duracao"],
                        est["kc"],
                        est["id"],
                        qtd_estagios
                    ])
            return linhas
        else:
            resposta = self.supabase.table(nome_tabela).select("*").execute()
            if not resposta.data:
                return []
            # Converter dicts em lista de listas (respeitando ordem de colunas)
            colunas = list(resposta.data[0].keys())
            return [[linha[col] for col in colunas] for linha in resposta.data]








if __name__ == "__main__":
    db = DatabaseManager(url, key)
    print(db.usuario("abc@gmail.com"))

