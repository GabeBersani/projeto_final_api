from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError
import datetime
from flask_login import UserMixin
Base = declarative_base()
engine = create_engine('sqlite:///database.db')
SessionLocal = sessionmaker(bind=engine)
def local_session():
    return SessionLocal()



class Usuario(UserMixin, Base):
    __tablename__ = 'USUARIO'

    id_usuario = Column(Integer, primary_key=True)
    nome = Column(String(40), nullable=False)
    email = Column(String, nullable=False, unique=True)
    senha_hash = Column(String, nullable=False)
    papel = Column(String, default='aluno', nullable=False)

    def __init__(self, nome, email, senha_hash = None, papel='aluno'):
        self.nome = nome
        self.email = email
        self.senha_hash = senha_hash
        self.papel = papel

    def set_senha_hash(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def serialize_usuario(self):
        return {
            'id_usuario': self.id_usuario,
            'nome': self.nome,
            'email': self.email,
            'papel': self.papel,
        }


class Alimento(Base):
    __tablename__ = 'ALIMENTO'

    id_alimento = Column(Integer, primary_key=True)
    nome = Column(String(40), nullable=False, index=True, unique=True)
    valor = Column(Float, nullable=False)
    quantidade = Column(Integer, nullable=False)
    categoria = Column(String, nullable=False)
    marca = Column(String, nullable=False)
    descricao = Column(String, nullable=False)

    pedidos = relationship("Pedido", back_populates="alimento")

    def __repr__(self):
        return '<Alimento: {} {} R${:.2f}>'.format(self.id_alimento, self.nome, self.valor)

    def serialize_alimento(self):
        return {
            'id_alimento': self.id_alimento,
            'nome': self.nome,
            'valor': self.valor,
            'quantidade': self.quantidade,
            'categoria': self.categoria,
            'marca': self.marca,
            'descricao': self.descricao,
        }


class Pedido(Base):
    __tablename__ = 'PEDIDO'

    id_pedido = Column(Integer, primary_key=True)
    nome_aluno = Column(String(40), nullable=False)
    nome_pedido = Column(String(40), nullable=False)
    valor_pedido = Column(Float, nullable=False)
    quantidade_pedido = Column(Integer, nullable=False)
    id_alimento = Column(Integer, ForeignKey('ALIMENTO.id_alimento'), nullable=False)
    alimento = relationship("Alimento", back_populates="pedidos")
    status_pagamento = Column(String, default='pendente', nullable=False)

    def __repr__(self):
        return '<Pedido: {} {} (Aluno: {})>'.format(self.id_pedido, self.nome_pedido, self.nome_aluno)

    def serialize_pedido(self):
        return {
            'id_pedido': self.id_pedido,
            'nome_aluno': self.nome_aluno,
            'nome_pedido': self.nome_pedido,
            'valor_pedido': self.valor_pedido,
            'quantidade_pedido': self.quantidade_pedido,
            'id_alimento': self.id_alimento,
            'status_pagamento': self.status_pagamento,
        }

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("Tabelas criadas com sucesso ou já existentes.")
    except SQLAlchemyError as e:
        print(f"Erro ao inicializar o banco de dados: {e}")


if __name__ == '__main__':
    init_db()