import pymysql
from urllib.parse import urlparse
import hashlib


def sha256(texto):
    sha = hashlib.sha256()
    sha.update(texto.encode('utf-8'))
    return sha.hexdigest()


class DatabaseManager:
    def __init__(self, db_url):
        self.db_url = db_url
    
    
        self.executar("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            senha_hash CHAR(64) NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        self.executar("""
        CREATE TABLE IF NOT EXISTS solos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            capacidade_campo FLOAT NOT NULL,
            ponto_murcha FLOAT NOT NULL,
            densidade FLOAT NOT NULL,
            porosidade FLOAT NOT NULL,
            cond_hidraulica ENUM('Baixa', 'Média', 'Alta') NOT NULL
        );
        """)
        
        self.executar("""
        CREATE TABLE IF NOT EXISTS culturas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL
        );
        """)
        
        self.executar("""
        CREATE TABLE IF NOT EXISTS estagios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cultura_id INT NOT NULL,
            nome VARCHAR(100) NOT NULL,
            numero_estagio INT NOT NULL,
            duracao INT NOT NULL,
            kc FLOAT NOT NULL,
            
            
            FOREIGN KEY (cultura_id) REFERENCES culturas(id) ON DELETE CASCADE
        );
        """)
        
        self.executar("""
        CREATE TABLE IF NOT EXISTS hortas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            usuario_id INT NOT NULL,
            tamanho FLOAT NOT NULL,
            duracao INT NOT NULL,
            solo_id INT NOT NULL,
            estagio_id INT NOT NULL,
            chave VARCHAR(36) UNIQUE NOT NULL DEFAULT (UUID()),

            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (solo_id) REFERENCES solos(id),
            FOREIGN KEY (estagio_id) REFERENCES estagios(id)
        );
        """)
        
        
    def conectar_banco_de_dados(self):
        parsed_url = urlparse(self.db_url)
        
        # Conexão com o MySQL utilizando PyMySQL
        conexão = pymysql.connect(
            user=parsed_url.username,
            password=parsed_url.password,
            host=parsed_url.hostname,
            port=parsed_url.port,
            database=parsed_url.path.lstrip('/'),
            autocommit=True  # Habilitar autocommit para evitar a necessidade de commit explícito
        )
        return conexão

    def executar(self, query):
        # Função para executar queries
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
        self.executar(f"""INSERT INTO usuarios (email, senha_hash)
                        VALUES ('{email}', '{senha}');
                        """)
        
    
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
        SELECT hortas.id, hortas.tamanho, culturas.nome, solos.nome, hortas.chave
        FROM hortas
        JOIN usuarios ON hortas.usuario_id = usuarios.id
        JOIN estagios on hortas.estagio_id = estagios.id
        JOIN culturas ON estagios.cultura_id = culturas.id
        JOIN solos ON hortas.solo_id = solos.id
        WHERE usuarios.email = %s;
        """
        
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query, (email,))
        
        hortas = cursor.fetchall()
        
        cursor.close()
        conexão.close()
        
        return hortas
    
    
    def culturas(self):
        query = "SELECT MIN(id) AS id, nome FROM culturas GROUP BY nome;"
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query)
        culturas = cursor.fetchall()
        cursor.close()
        conexão.close()
        return culturas


    def solos(self):
        query = "SELECT id, nome FROM solos;"
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query)
        solos = cursor.fetchall()
        cursor.close()
        conexão.close()
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

        return None




        
    def adicionar_horta(self, usuario, tamanho, cultura, solo, tempo):
        estagio_id = self.estagio(cultura, tempo)
        if estagio_id != None:
            self.executar(f"""INSERT INTO hortas (usuario_id, tamanho, duracao, solo_id, estagio_id) VALUES 
                            ({usuario}, {tamanho}, {tempo}, {solo}, {estagio_id})""")
            return True
        return False
        
        
    def imprimir_tabela(self, nome_tabela):
        query = f"SELECT * FROM {nome_tabela};"
        
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query)
        
        linhas = cursor.fetchall()
        
        for linha in linhas:
            print(linha)
        
        cursor.close()
        conexão.close()

#db.executar("""INSERT INTO usuarios (email, senha_hash) VALUES ('flaviomaurilio0@gmail.com', '12345')""")
#db.executar("""INSERT INTO solos (nome, capacidade_campo, ponto_murcha, densidade, porosidade, cond_hidraulica) VALUES ('Arenoso-argiloso', 150, 175, 1.65, 0.35, 'Alta')""")
#db.executar("""INSERT INTO culturas (nome, estagio, numero_estagio, tempo, kc) VALUES ('Coentro', 'final', 3, 10, 0.5)""")

if __name__ == "__main__":
    db_url = "mysql://root:ajNlmcyIPZQVSGsTkLXFRDjmpkNzkQTw@hopper.proxy.rlwy.net:22040/railway"
    db = DatabaseManager(db_url)
    db.executar("drop table hortas")
    