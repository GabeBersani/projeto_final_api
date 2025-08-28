from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, DateTime, Float
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.orm import sessionmaker, declarative_base
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()
engine = create_engine('sqlite:///database.db')
SessionLocalExemplo = sessionmaker(bind=engine)

class Funcionario(Base):
    __tablename__ = 'funcionario'
    id = Column(Integer, primary_key=True)
    nome_funcionario = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    senha_hash = Column(String, nullable=False)
    papel = Column(String, default="funcionario")

    def set_senha_hash(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def serialize(self):
        dados={
            'id': self.id,
            'nome_funcionario': self.nome_funcionario,
            'email': self.email,
            'papel': self.papel,
        }
        return dados


class NotasExemplo(Base):
    __tablename__ = 'notas_exemplo'
    id = Column(Integer, primary_key=True)
    conteudo = Column(String, nullable=False)
    # user_id = Column(Integer, ForeignKey('usuarios_exemplo.id')) # Poderia ter para associar

class Aluno(Base):
    __tablename__ = 'ALUNO'
    id_aluno = Column(Integer, primary_key=True)
    nome = Column(String(40), nullable=False, index=True)
    CPF = Column(String(11), nullable=False, index=True, unique=True)
    email = Column(String, nullable=False, unique=True)
    senha_hash = Column(String, nullable=False)
    papel = Column(String, default="aluno")

    def set_senha_hash(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def serialize(self):
        dados = {
            'id_aluno': self.id_aluno,
            'nome': self.nome,
            'email': self.email,
            'papel': self.papel,
        }
        return dados

class Salgado(Base):
    __tablename__ = 'SALGADO'
    id_salgado = Column(Integer, primary_key=True)
    nome_salgado = Column(String(40), nullable=False, index=True)
    valor_salgado = Column(Float, nullable=False)
    quantidade_salgado = Column(Integer, nullable=False)

    def __repr__(self):
        return '<Emprestimo: {} {} {}>'.format(self.id_salgado, self.nome_salgado, self.valor_salgado,
                                               self.quantidade_salgado)

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except SQLAlchemyError:
            db_session.rollback()
            raise

    def delete(self, db_session):
        db_session.delete(self)
        db_session.commit()


    def serialize_emprestimo(self):
        return {
            "nome salgado": self.nome_salgado,
            "valor salgado": self.valor_salgado,
            "quantidade salgado": self.quantidade_salgado,
        }

class Doce(Base):
    __tablename__ = 'DOCE'
    id_doce = Column(Integer, primary_key=True)
    nome_doce = Column(String(40), nullable=False, index=True)
    valor_doce = Column(Float, nullable=False)
    quantidade_doce = Column(Integer, nullable=False)

    def __repr__(self):
        return '<Emprestimo: {} {} {}>'.format(self.id_doce, self.nome_doce, self.valor_doce,
                                               self.quantidade_doce)

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except SQLAlchemyError:
            db_session.rollback()
            raise

    def delete(self, db_session):
        db_session.delete(self)
        db_session.commit()


    def serialize_emprestimo(self):
        return {
            "nome salgado": self.nome_doce,
            "valor doce": self.valor_doce,
            "quantidade doce": self.quantidade_doce,
        }

class Bebida(Base):
    __tablename__ = 'BEBIDA'
    id_bebida = Column(Integer, primary_key=True)
    nome_bebida = Column(String(40), nullable=False, index=True)
    valor_bebida = Column(Float, nullable=False)
    quantidade_bebida = Column(Integer, nullable=False)

    def __repr__(self):
        return '<Emprestimo: {} {} {}>'.format(self.id_bebida, self.nome_bebida, self.valor_bebida,
                                               self.quantidade_bebida)

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except SQLAlchemyError:
            db_session.rollback()
            raise

    def delete(self, db_session):
        db_session.delete(self)
        db_session.commit()


    def serialize_emprestimo(self):
        return {
            "nome bebida": self.nome_bebida,
            "valor bebida": self.valor_bebida,
            "quantidade bebida": self.quantidade_bebida,
        }

class Pedido(Base):
    __tablename__ = 'PEDIDO'
    id_pedido = Column(Integer, primary_key=True)
    nome_aluno = Column(String(40), nullable=False, index=True)
    nome_pedido = Column(String(40), nullable=False, index=True)
    valor_pedido = Column(Float, nullable=False)
    quantidade_pedido = Column(Integer, nullable=False)

    def __repr__(self):
        return '<Emprestimo: {} {} {}>'.format(self.id_pedido, self.nome_pedido, self.nome_aluno,
                                               self.valor_pedido, self.quantidade_pedido)

    def save(self, db_session):
        try:
            db_session.add(self)
            db_session.commit()
        except SQLAlchemyError:
            db_session.rollback()
            raise

    def delete(self, db_session):
        db_session.delete(self)
        db_session.commit()


    def serialize_emprestimo(self):
        return {
            "nome aluno": self.nome_aluno,
            "nome pedido": self.nome_pedido,
            "valor pedido": self.valor_pedido,
            "quantidade pedido": self.quantidade_pedido,
        }
def init_db():
    Base.metadata.create_all(bind=engine)
if __name__ == '__main__':
    init_db()
