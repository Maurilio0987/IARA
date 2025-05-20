import pg8000
from urllib.parse import urlparse
import hashlib

# postgresql://iara_database_e7zl_user:2FW7U5MdZnj0b88ufN2HBrB6kcWuJQYg@dpg-d0ku70vfte5s73917eng-a.oregon-postgres.render.com/iara_database_e7zl

def sha256(texto):
    sha = hashlib.sha256()
    sha.update(texto.encode('utf-8'))
    return sha.hexdigest()


class DatabaseManager:
    def __init__(self, db_url):
        self.db_url = db_url
    
        # Requer a extensão "pgcrypto" para usar gen_random_uuid()
        self.executar("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

        self.executar("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            senha_hash CHAR(64) NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.executar("""
        CREATE TABLE IF NOT EXISTS solos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            capacidade_campo FLOAT NOT NULL,
            ponto_murcha FLOAT NOT NULL,
            densidade FLOAT NOT NULL,
            porosidade FLOAT NOT NULL,
            cond_hidraulica TEXT NOT NULL CHECK (cond_hidraulica IN ('Baixa', 'Média', 'Alta'))
        )
        """)

        self.executar("""
        CREATE TABLE IF NOT EXISTS culturas (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL
        )
        """)

        self.executar("""
        CREATE TABLE IF NOT EXISTS estagios (
            id SERIAL PRIMARY KEY,
            cultura_id INT NOT NULL REFERENCES culturas(id) ON DELETE CASCADE,
            nome VARCHAR(100) NOT NULL,
            numero_estagio INT NOT NULL,
            duracao INT NOT NULL,
            kc FLOAT NOT NULL
        )
        """)

        self.executar("""
        CREATE TABLE IF NOT EXISTS hortas (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            usuario_id INT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            tamanho FLOAT NOT NULL,
            duracao INT NOT NULL,
            solo_id INT NOT NULL REFERENCES solos(id),
            estagio_id INT NOT NULL REFERENCES estagios(id),
            historico JSON NOT NULL,
            chave UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
            volume FLOAT DEFAULT 0,
            volume_irrigado FLOAT DEFAULT 0
        )
        """)
        
        
    def conectar_banco_de_dados(self):
        parsed_url = urlparse(self.db_url)

        conexão = pg8000.connect(
            user=parsed_url.username,
            password=parsed_url.password,
            host=parsed_url.hostname,
            port=parsed_url.port or 5432,
            database=parsed_url.path.lstrip('/'),
            ssl_context=True  # Render exige SSL
        )
        conexão.autocommit = True  # Ativa autocommit
        return conexão

    
    def executar(self, query):
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query)
        cursor.close()
        conexão.close()


    def verificar_email(self, email):
        query = "SELECT EXISTS (SELECT 1 FROM usuarios WHERE email = %s);"
        
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query, (email,))
        resultado = cursor.fetchone()
        cursor.close()
        conexão.close()
        
        return resultado[0]


    def verificar_senha(self, email, senha):
        query = "SELECT senha_hash FROM usuarios WHERE email = %s;"
        
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query, (email,))
        resultado = cursor.fetchone()
        cursor.close()
        conexão.close()
        
        if resultado:
            return resultado[0] == senha
        else:
            return False

    def adicionar_usuario(self, email, senha):
        query = "INSERT INTO usuarios (email, senha_hash) VALUES (%s, %s);"
        
        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query, (email, senha))
        cursor.close()
        conexao.close()


    def usuario(self, email):
        query = "SELECT id FROM usuarios WHERE email = %s;"
        
        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query, (email,))
        resultado = cursor.fetchone()
        cursor.close()
        conexao.close()

        return resultado[0] if resultado else None

    def hortas(self, email):
        query = """
        SELECT hortas.id, hortas.nome, hortas.chave, hortas.tamanho, culturas.nome, solos.nome
        FROM hortas
        JOIN usuarios ON hortas.usuario_id = usuarios.id
        JOIN estagios ON hortas.estagio_id = estagios.id
        JOIN culturas ON estagios.cultura_id = culturas.id
        JOIN solos ON hortas.solo_id = solos.id
        WHERE usuarios.email = %s;
        """

        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query, (email,))
        hortas = cursor.fetchall()
        cursor.close()
        conexao.close()

        return hortas

    def horta(self, chave):
        query = """
        SELECT hortas.id, hortas.nome, hortas.tamanho, culturas.nome, solos.nome,
               hortas.chave, estagios.nome, hortas.duracao, estagios.kc
        FROM hortas
        JOIN usuarios ON hortas.usuario_id = usuarios.id
        JOIN estagios ON hortas.estagio_id = estagios.id
        JOIN culturas ON estagios.cultura_id = culturas.id
        JOIN solos ON hortas.solo_id = solos.id
        WHERE hortas.chave = %s;
        """

        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query, (chave,))
        horta = cursor.fetchone()
        cursor.close()
        conexao.close()

        return horta

    def remover_horta(self, chave):
        query = "DELETE FROM hortas WHERE chave = %s"
        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query, (chave,))
        cursor.close()
        conexao.close()


    def remover_cultura(self, id):
        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()

        # Obtém o cultura_id do estágio
        cursor.execute("SELECT cultura_id FROM estagios WHERE id = %s", (id,))
        resultado = cursor.fetchone()

        if not resultado:
            cursor.close()
            conexao.close()
            raise ValueError("Estágio não encontrado.")

        cultura_id = resultado[0]

        # Remove o estágio
        cursor.execute("DELETE FROM estagios WHERE id = %s", (id,))

        # Verifica se ainda há estágios para essa cultura
        cursor.execute("SELECT COUNT(*) FROM estagios WHERE cultura_id = %s", (cultura_id,))
        quantidade = cursor.fetchone()[0]

        if quantidade == 0:
            # Remove a cultura se não houver mais estágios
            cursor.execute("DELETE FROM culturas WHERE id = %s", (cultura_id,))
        else:
            # Reordena os números dos estágios restantes
            cursor.execute(
                "SELECT id FROM estagios WHERE cultura_id = %s ORDER BY numero_estagio",
                (cultura_id,)
            )
            estagios_restantes = cursor.fetchall()

            for novo_numero, (estagio_id,) in enumerate(estagios_restantes, start=1):
                cursor.execute(
                    "UPDATE estagios SET numero_estagio = %s WHERE id = %s",
                    (novo_numero, estagio_id)
                )

        cursor.close()
        conexao.close()
  

    def culturas(self):
        query = "SELECT MIN(id) AS id, nome FROM culturas GROUP BY nome;"
        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query)
        culturas = cursor.fetchall()
        cursor.close()
        conexao.close()
        return culturas


    def solos(self):
        query = "SELECT id, nome FROM solos;"
        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query)
        solos = cursor.fetchall()
        cursor.close()
        conexao.close()
        return solos


    def estagio(self, cultura_id, tempo):
        query = """
        SELECT id, duracao FROM estagios
        WHERE cultura_id = %s
        ORDER BY numero_estagio;
        """

        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query, (cultura_id,))
        estagios = cursor.fetchall()
        cursor.close()
        conexao.close()

        tempo_acumulado = 0
        for estagio_id, duracao in estagios:
            tempo_acumulado += duracao
            if tempo <= tempo_acumulado:
                return estagio_id

        return estagio_id  # Retorna o último estágio se tempo for maior que a soma

    def chaves(self):
        query = "SELECT chave FROM hortas;"
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query)
        chaves = cursor.fetchall()
        cursor.close()
        conexão.close()
        return chaves

    def volumes(self, chave):
        query = "SELECT volume, volume_irrigado FROM hortas WHERE chave = %s;"
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query, (chave,))
        volumes = cursor.fetchone()
        cursor.close()
        conexão.close()
        return volumes

    def adicionar_volume_irrigado(self, chave, valor):
        query = "UPDATE hortas SET volume_irrigado = volume_irrigado + %s WHERE chave = %s;"
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query, (valor, chave))
        cursor.close()
        conexão.close()

    def adicionar_volume(self, chave, valor):
        query = "UPDATE hortas SET volume = volume + %s WHERE chave = %s;"
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query, (valor, chave))
        cursor.close()
        conexão.close()

    def zerar_volumes(self, chave):
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        
        # PostgreSQL usa jsonb_array_append para JSON, mas precisa ser refeito manualmente
        cursor.execute("SELECT historico, volume_irrigado FROM hortas WHERE chave = %s", (chave))
        resultado = cursor.fetchone()

        if resultado:
            historico, volume_irrigado = resultado
            if historico and isinstance(historico, list):
                historico = historico[1:] + [volume_irrigado]
            else:
                historico = [volume_irrigado]

            cursor.execute("UPDATE hortas SET historico = %s, volume_irrigado = 0, volume = 0 WHERE chave = %s",
                           (historico, chave))

        cursor.close()
        conexão.close()

    def historico(self, chave):
        query = "SELECT historico, volume_irrigado FROM hortas WHERE chave = %s;"
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query, (chave,))
        historico = cursor.fetchone()
        cursor.close()
        conexão.close()
        return historico

    def adicionar_horta(self, usuario, nome, tamanho, cultura, solo, tempo):
        estagio_id = self.estagio(cultura, tempo)
        if estagio_id is not None:
            query = """
            INSERT INTO hortas (usuario_id, nome, tamanho, duracao, solo_id, estagio_id, historico)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
            historico_inicial = "[0,0,0,0,0,0]"
            conexão = self.conectar_banco_de_dados()
            cursor = conexão.cursor()
            cursor.execute(query, (usuario, nome, tamanho, tempo, solo, estagio_id, historico_inicial))
            cursor.close()
            conexão.close()
            return True
        return False

    def atualizar_hortas(self):
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()

        cursor.execute("UPDATE hortas SET duracao = duracao + 1;")
        cursor.execute("SELECT id, duracao, estagio_id FROM hortas;")
        hortas = cursor.fetchall()

        for horta_id, duracao, estagio_id in hortas:
            cursor.execute("SELECT cultura_id FROM estagios WHERE id = %s;", (estagio_id,))
            cultura_id = cursor.fetchone()

            if not cultura_id:
                continue

            cultura_id = cultura_id[0]
            novo_estagio_id = self.estagio(cultura_id, duracao)

            if novo_estagio_id and novo_estagio_id != estagio_id:
                cursor.execute("UPDATE hortas SET estagio_id = %s WHERE id = %s;", (novo_estagio_id, horta_id))

        cursor.close()
        conexão.close()

    def tabela(self, nome_tabela):
        if nome_tabela == "culturas":
            query = """
            SELECT 
                cultura.nome AS cultura,
                estagio.nome AS estagio,
                estagio.duracao,
                estagio.kc,
                estagio.id,
                sub.qtd_estagios
            FROM culturas cultura
            JOIN estagios estagio ON cultura.id = estagio.cultura_id
            JOIN (
                SELECT cultura_id, COUNT(*) AS qtd_estagios
                FROM estagios
                GROUP BY cultura_id
            ) sub ON cultura.id = sub.cultura_id
            ORDER BY cultura.nome, estagio.numero_estagio;
            """
        else:
            query = f"SELECT * FROM {nome_tabela};"

        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query)
        linhas = cursor.fetchall()
        cursor.close()
        conexão.close()
        return linhas

    def adicionar_solo(self, nome, capacidade_campo, ponto_murcha, densidade, porosidade, cond_hidraulica):
        query = """
        INSERT INTO solos (nome, capacidade_campo, ponto_murcha, densidade, porosidade, cond_hidraulica)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query, (nome, capacidade_campo, ponto_murcha, densidade, porosidade, cond_hidraulica))
        cursor.close()
        conexão.close()

    def adicionar_cultura(self, nome, estagio, duracao, kc):
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()

        nome = nome.capitalize()
        estagio = estagio.capitalize()

        cursor.execute("SELECT id FROM culturas WHERE nome = %s", (nome,))
        cultura_existente = cursor.fetchone()

        if cultura_existente:
            cultura_id = cultura_existente[0]
        else:
            cursor.execute("INSERT INTO culturas (nome) VALUES (%s)", (nome,))
            cursor.execute("SELECT id FROM culturas WHERE nome = %s ORDER BY id DESC LIMIT 1", (nome,))
            cultura_id = cursor.fetchone()[0]

        cursor.execute("SELECT MAX(numero_estagio) FROM estagios WHERE cultura_id = %s", (cultura_id,))
        ultimo_estagio = cursor.fetchone()
        proximo_numero = (ultimo_estagio[0] or 0) + 1

        cursor.execute(
            "INSERT INTO estagios (cultura_id, numero_estagio, nome, duracao, kc) VALUES (%s, %s, %s, %s, %s)",
            (cultura_id, proximo_numero, estagio, duracao, kc)
        )

        cursor.close()
        conexão.close()



if __name__ == "__main__":
    db_url = "postgresql://iara_database_e7zl_user:2FW7U5MdZnj0b88ufN2HBrB6kcWuJQYg@dpg-d0ku70vfte5s73917eng-a.oregon-postgres.render.com/iara_database_e7zl"
    db = DatabaseManager(db_url)
    
