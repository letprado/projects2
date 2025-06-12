#!/usr/bin/env python3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from safrs import SAFRSBase, SafrsApi

db = SQLAlchemy()

# Example SQLAlchemy database objects
class Usuario(SAFRSBase, db.Model):
    """
    Descrição: descrição do usuário
    """
    __tablename__ = "Usuarios"
    id = db.Column(db.String, primary_key=True)
    nome = db.Column(db.String, default="")
    email = db.Column(db.String, default="")
    faculdade = db.relationship("Faculdade", back_populates="usuario", lazy="dynamic")


class Faculdade(SAFRSBase, db.Model):
    """
    Faculdade: descrição da faculdade
    """
    __tablename__ = "Faculdades"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, default="")
    usuario_id = db.Column(db.String, db.ForeignKey("Usuarios.id")) #corrigido: nome certo da tabela
    usuario = db.relationship("Usuario", back_populates="faculdade")


# Create the API endpoints
def create_api(app, host="127.0.0.1", port=5030, api_prefix="/api"):
    api = SafrsApi(app, host=host, port=port, prefix=api_prefix)
    api.expose_object(Usuario) #Ei SAFRS, por favor crie um endpoint para que o mundo consiga acessar, criar, editar e deletar dados desse modelo via internet
    api.expose_object(Faculdade) #2
    print(f"Created API: http://{host}:{port}/{api_prefix}")


def create_app(host="127.0.0.1", port=5030):
    app = Flask("teste_swagger")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    db.init_app(app)

    with app.app_context():
        db.create_all()
        create_api(app, host, port)
        for i in range(200):
            usuario_exemplo = Usuario(nome=f"usuario{i}", email=f"email{i}@email.com") #evitar conflito de nome com a classe
            faculdade_exemplo = Faculdade(nome=f"test faculdade {i}")
             #faculdade.usuario_id vai automaticamente ser o id do usuario.
             #usuario.faculdade vai conter a faculdade do usuario.
            usuario_exemplo.faculdade.append(faculdade_exemplo) #Adiciona essa faculdade na lista de faculdades do usuário.
    return app


# Configurações fixas para evitar erros
HOST = "127.0.0.1"
PORT = 5030
app = create_app(host=HOST, port=PORT)

if __name__ == "__main__": #Execute o que está dentro somente se esse arquivo for executado diretamente
    app.run(host=HOST, port=PORT)
    #host="127.0.0.1" → só acessível do seu computador (localhost).
    #port=5030 → a porta da aplicação (pode ser outra, tipo 5000 ou 8000)
