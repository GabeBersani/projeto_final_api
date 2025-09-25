from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, declarative_base
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()
engine = create_engine('sqlite:///database.db')
local_session = sessionmaker(bind=engine)

class Usuario(Base):
    __tablename__ = 'USUARIO'

    id_usuario = Column(Integer, primary_key=True)
    nome = Column(String(40), nullable=False, index=True)
    cpf = Column(String(11), nullable=False, index=True, unique=True)
    email = Column(String, nullable=False, unique=True)
    senha_hash = Column(String, nullable=False)
    papel = Column(String, default='aluno')  # Pode ser "aluno" ou "funcionario"

    def set_senha_hash(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def serialize_usuario(self):
        return {
            'id_usuario': self.id_usuario,
            'nome': self.nome,
            'cpf': self.cpf,
            'email': self.email,
            'papel': self.papel,
        }

class Alimento(Base):
    __tablename__ = 'ALIMENTO'

    id_alimento = Column(Integer, primary_key=True)
    nome = Column(String(40), nullable=False, index=True, unique=True)
    valor = Column(Float, nullable=False)
    quantidade = Column(Integer, nullable=False)
    categoria = Column(String, nullable=False)  # 'bebida', 'doce', 'salgado'
    marca = Column(String, nullable=False)
    descricao = Column(String, nullable=False)

    def __repr__(self):
        return '<Alimento: {} {} R${:.2f}>'.format(self.id_alimento, self.nome, self.valor)

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except SQLAlchemyError:
            db_session.rollback()
            raise

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except SQLAlchemyError:
            db_session.rollback()
            raise

    def serialize_alimento(self):
        return {
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
    nome_aluno = Column(String(40), nullable=False, index=True)
    nome_pedido = Column(String(40), nullable=False, index=True)
    valor_pedido = Column(Float, nullable=False)
    quantidade_pedido = Column(Integer, nullable=False)

    def __repr__(self):
        return '<Pedido: {} {} (Aluno: {})>'.format(self.id_pedido, self.nome_pedido, self.nome_aluno)

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except SQLAlchemyError:
            db_session.rollback()
            raise

    def delete(self, db_session):
        try:
            db_session.delete(self)
            db_session.commit()
        except SQLAlchemyError:
            db_session.rollback()
            raise

    def serialize_pedido(self):
        return {
            'nome_aluno': self.nome_aluno,
            'nome_pedido': self.nome_pedido,
            'valor_pedido': self.valor_pedido,
            'quantidade_pedido': self.quantidade_pedido,
        }

def init_db():
    Base.metadata.create_all(bind=engine)
if __name__ == '__main__':
    init_db()
