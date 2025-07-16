from supabase import create_client, Client
import hashlib


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


if __name__ == "__main__":
    db = DatabaseManager(url, key)
    print(db.verificar_email("abc@gmail.com"))
    print(db.verificar_senha("abc@gmail.com", "abc123"))

    print(db.verificar_senha("abc@gmail.com", "Cccc"))