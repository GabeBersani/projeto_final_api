import logging
from functools import wraps
# from tkinter.tix import Select

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import get_jwt_identity, JWTManager, create_access_token, jwt_required
from flask_pydantic_spec import FlaskPydanticSpec
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from werkzeug.security import check_password_hash

from models import Usuario, Alimento, Pedido, local_session, init_db


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super_senha"
app.config['JWT_SECRET_KEY'] = 'super_senha'
jwt = JWTManager(app)
CORS(app)
spec = FlaskPydanticSpec('flask', title='API - AROMA & SABOR', version='1.0.0')

# login_manager = LoginManager()
# login_manager.init_app(app)

# @login_manager.user_loader
# def load_user(user_id):
#     db_session = local_session()
#     sql = db_session.execute(select(Usuario).filter_by(id=user_id))
#     return sql.get(int(user_id))
#
# def validar_usuario(email, senha):
#     sql = select(Usuario).filter_by(email=email)
#     if not sql:
#         return None
#     if check_password_hash(sql.senha, senha):
#         return sql



def admin_required(fn):
    """Protege a rota, exigindo que o usuário logado tenha o papel de 'funcionario'."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_email = get_jwt_identity()
        db = local_session()
        try:
            user = db.execute(select(Usuario).where(Usuario.email == current_user_email)).scalar_one_or_none()

            if user and user.papel == "funcionario":
                return fn(*args, **kwargs)
            return jsonify(msg="Acesso negado: Requer privilégios de funcionário"), 403
        except Exception as e:
            logging.error(f"Erro na autorização do funcionário: {e}")
            return jsonify(msg="Erro ao verificar privilégios"), 500
        finally:
            db.close()

    return wrapper


@app.route('/')
def index():
    return jsonify({'message': 'Welcome to Exemplo API!'})

@app.route('/login', methods=['POST'])
def login():
    dados = request.get_json()
    email = dados.get('email')
    senha = dados.get('senha')

    if not email or not senha:
        return jsonify({"msg": "Email e senha obrigatórios"}), 400

    db = local_session()
    try:
        user = db.execute(select(Usuario).where(Usuario.email == email)).scalar_one_or_none()

        if user and user.check_password(senha):
            access_token = create_access_token(identity=str(user.email))
            return jsonify({
                "access_token": access_token,
                "papel": user.papel,
            }), 200

        return jsonify({"msg": "Credenciais inválidas"}), 401

    except Exception as e:
        logging.error(f"Erro no login: {e}")
        return jsonify({"msg": "Erro interno do servidor"}), 500

    finally:
        db.close()


@app.route('/alunos', methods=['GET'])
# @jwt_required()
def lista_usuarios():
    db = local_session()
    try:
        tds_usuarios = db.execute(select(Usuario)).scalars().all()
        lista_usuarios = [usuario.serialize_usuario() for usuario in tds_usuarios]
        print(lista_usuarios)
        return jsonify({"usuarios": lista_usuarios}), 200

    except Exception as e:
        logging.error(f"Erro ao listar usuários: {e}")
        return jsonify({"msg": "Erro interno ao listar usuários"}), 500

    finally:
        db.close()


@app.route('/usuarios', methods=['POST'])
def cadastro_usuarios():

    dados = request.get_json()
    nome = dados.get('nome')
    email = dados.get('email')
    papel = dados.get('papel', 'aluno')
    senha = dados.get('senha')

    if not nome or not email or not senha:
        return jsonify({"msg": "Nome, email e senha são obrigatórios"}), 400

    if papel.lower() == "aluno" and not email.lower().endswith("@aluno"):
        return jsonify({"msg": "Email de aluno deve terminar com '@aluno' se o papel for 'aluno'"}), 400

    db = local_session()
    try:
        if db.execute(select(Usuario).where(Usuario.email == email)).scalar_one_or_none():
            return jsonify({"msg": "Usuário com esse email já existe"}), 400
        novo_usuario = Usuario(nome=nome, email=email, papel=papel)
        novo_usuario.set_senha_hash(senha)

        db.add(novo_usuario)
        db.commit()

        return jsonify({
            "msg": "Usuário criado com sucesso",
            "user_id": novo_usuario.id_usuario
        }), 201

    except IntegrityError:
        db.rollback()
        return jsonify({"msg": "Erro de integridade (e-mail duplicado)"}), 400

    except Exception as e:
        db.rollback()
        logging.error(f"Erro ao registrar usuário: {e}")
        return jsonify({"msg": "Erro interno ao registrar usuário"}), 500

    finally:
        db.close()


@app.route('/editar_usuario/<int:id>', methods=['PUT'])
@jwt_required()
def editar_usuario(id):
    """Edita os dados de um usuário. CPF removido."""
    dados = request.get_json()
    db = local_session()

    try:
        usuario = db.execute(select(Usuario).where(Usuario.id_usuario == id)).scalar_one_or_none()
        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404

        updated = False

        if 'nome' in dados and dados['nome'] is not None:
            usuario.nome = dados['nome']
            updated = True

        if 'email' in dados and dados['email'] is not None and dados['email'] != usuario.email:
            # Valida e-mail duplicado
            if db.execute(select(Usuario).where(Usuario.email == dados['email'])).scalar_one_or_none():
                return jsonify({"msg": "Novo email já está em uso"}), 400
            usuario.email = dados['email']
            updated = True

        if 'papel' in dados and dados['papel'] is not None:
            usuario.papel = dados['papel']
            updated = True

        if 'senha' in dados and dados['senha'] is not None:
            usuario.set_senha_hash(dados['senha'])
            updated = True

        if updated:
            db.commit()
            return jsonify(usuario.serialize_usuario()), 200

        return jsonify({"msg": "Nenhuma alteração realizada"}), 200

    except Exception as e:
        db.rollback()
        logging.error(f"Erro ao editar usuário: {e}")
        return jsonify({'erro': "Erro interno ao editar usuário"}), 500

    finally:
        db.close()

@app.route('/alimento', methods=['GET'])
def get_alimento():
    db = local_session()
    try:
        resultado_alimento = db.execute(select(Alimento)).scalars().all()
        lista_alimento = [alimento.serialize_alimento() for alimento in resultado_alimento]
        return jsonify({'alimento': lista_alimento}), 200

    except Exception as e:
        logging.error(f"Erro ao listar alimentos: {e}")
        return jsonify({'erro': "Erro interno ao listar alimentos"}), 500

    finally:
        db.close()


@app.route('/novo_alimento', methods=['POST'])
@jwt_required()
@admin_required
def cadastrar_alimento():
    dados = request.get_json()
    db = local_session()
    try:
        campos = ['nome', 'valor', 'quantidade', 'marca', 'categoria', 'descricao']
        if not all(dados.get(c) is not None for c in campos):
            return jsonify({'erro': "Todos os campos são obrigatórios"}), 400

        categoria = dados['categoria'].lower()
        if categoria not in ['bebida', 'doce', 'salgado']:
            return jsonify({'erro': "Categoria inválida. Use: bebida, doce ou salgado"}), 400

        if db.execute(select(Alimento).where(Alimento.nome == dados['nome'])).scalar_one_or_none():
            return jsonify({'erro': "Alimento com este nome já existe"}), 400

        valor = float(dados['valor'])
        quantidade = int(dados['quantidade'])

        novo = Alimento(
            nome=dados['nome'],
            valor=valor,
            quantidade=quantidade,
            categoria=categoria,
            descricao=dados['descricao'],
            marca=dados['marca']
        )

        db.add(novo)
        db.commit()

        return jsonify(novo.serialize_alimento()), 201

    except (ValueError, TypeError):
        db.rollback()
        return jsonify({'erro': "Valor ou quantidade devem ser números válidos"}), 400

    except Exception as e:
        db.rollback()
        logging.error(f"Erro ao cadastrar alimento: {e}")
        return jsonify({'erro': "Erro interno ao cadastrar alimento"}), 500

    finally:
        db.close()


@app.route('/editar_alimento/<int:id>', methods=['PUT'])
@jwt_required()
@admin_required
def editar_alimento(id):
    dados = request.get_json()
    db = local_session()
    try:
        alimento = db.execute(select(Alimento).where(Alimento.id_alimento == id)).scalar_one_or_none()
        if not alimento:
            return jsonify({'erro': 'Alimento não encontrado'}), 404

        updated = False

        if 'nome' in dados and dados['nome'] is not None and dados['nome'] != alimento.nome:
            if db.execute(select(Alimento).where(Alimento.nome == dados['nome'])).scalar_one_or_none():
                return jsonify({'erro': "Nome de alimento já está em uso"}), 400
            alimento.nome = dados['nome']
            updated = True

        if 'valor' in dados and dados['valor'] is not None:
            alimento.valor = float(dados['valor'])
            updated = True

        if 'quantidade' in dados and dados['quantidade'] is not None:
            alimento.quantidade = int(dados['quantidade'])
            updated = True

        if 'categoria' in dados and dados['categoria'] is not None:
            categoria = dados['categoria'].lower()
            if categoria not in ['bebida', 'doce', 'salgado']:
                return jsonify({'erro': "Categoria inválida. Use: bebida, doce ou salgado"}), 400
            alimento.categoria = categoria
            updated = True

        if 'descricao' in dados and dados['descricao'] is not None:
            alimento.descricao = dados['descricao']
            updated = True

        if 'marca' in dados and dados['marca'] is not None:
            alimento.marca = dados['marca']
            updated = True

        if updated:
            db.commit()
            return jsonify(alimento.serialize_alimento()), 200

        return jsonify({"msg": "Nenhuma alteração realizada"}), 200

    except (ValueError, TypeError):
        db.rollback()
        return jsonify({'erro': "Valor ou quantidade devem ser números válidos"}), 400

    except Exception as e:
        db.rollback()
        logging.error(f"Erro ao editar alimento: {e}")
        return jsonify({'erro': "Erro interno ao editar alimento"}), 500

    finally:
        db.close()

@app.route('/pedido', methods=['GET'])
def get_pedido():
    db = local_session()
    try:
        resultado = db.execute(select(Pedido).options(joinedload(Pedido.alimento))).scalars().all()
        lista = [p.serialize_pedido() for p in resultado]
        return jsonify({'pedidos': lista}), 200

    except Exception as e:
        logging.error(f"Erro ao listar pedidos: {e}")
        return jsonify({'erro': "Erro interno ao listar pedidos"}), 500

    finally:
        db.close()


@app.route('/novo_pedido', methods=['POST'])
def cadastrar_pedido():
    dados = request.get_json()
    db = local_session()

    try:
        pedidos_recebidos = dados.get("pedidos")
        nome_aluno = dados.get("nome_aluno")

        if not pedidos_recebidos or not nome_aluno:
            return jsonify({'erro': "Dados incompletos: 'pedidos' e 'nome_aluno' são obrigatórios"}), 400

        novos_pedidos_serializados = []

        for item in pedidos_recebidos:
            if not all(k in item for k in ['nome', 'valor', 'quantidade']):
                db.rollback()
                return jsonify({'erro': "Cada item precisa de nome, valor e quantidade"}), 400

            try:
                valor = float(item['valor'])
                quantidade = int(item['quantidade'])
            except (ValueError, TypeError):
                db.rollback()
                return jsonify({'erro': "Valor ou quantidade de pedido inválidos"}), 400

            alimento = db.execute(select(Alimento).where(Alimento.nome == item['nome'])).scalar_one_or_none()
            if not alimento:
                db.rollback()
                return jsonify({'erro': f'Alimento {item["nome"]} não encontrado no estoque'}), 404

            if alimento.quantidade < quantidade:
                db.rollback()
                return jsonify(
                    {'erro': f'Estoque insuficiente para {alimento.nome}. Disponível: {alimento.quantidade}'}), 400

            novo = Pedido(
                nome_aluno=nome_aluno,
                nome_pedido=item['nome'],
                valor_pedido=valor,
                quantidade_pedido=quantidade,
                id_alimento=alimento.id_alimento,
            )
            db.add(novo)
            novos_pedidos_serializados.append(novo.serialize_pedido())

        db.commit()
        return jsonify({'msg': 'Pedidos cadastrados com sucesso', 'pedidos': novos_pedidos_serializados}), 201

    except Exception as e:
        db.rollback()
        logging.error(f"Erro ao cadastrar pedido: {e}")
        return jsonify({'erro': "Erro interno ao cadastrar pedido"}), 500

    finally:
        db.close()


@app.route('/finalizar_pedido/<int:id_pedido>', methods=['POST'])
@jwt_required()
@admin_required
def finalizar_pedido(id_pedido):
    dados = request.get_json()
    metodo = dados.get('metodo_pagamento')

    if not metodo:
        return jsonify({'erro': "Método de pagamento deve ser informado"}), 400

    metodo = metodo.lower()
    if metodo not in ['pix', 'dinheiro', 'cartao']:
        return jsonify({'erro': "Método de pagamento inválido. Use: pix, dinheiro ou cartao"}), 400

    db = local_session()

    try:
        pedido = db.execute(select(Pedido).where(Pedido.id_pedido == id_pedido)).scalar_one_or_none()
        if not pedido:
            return jsonify({'erro': "Pedido não encontrado"}), 404

        if pedido.status_pagamento == 'pago':
            return jsonify({'msg': 'Pedido já está pago.'}), 200

        alimento = db.get(Alimento, pedido.id_alimento)
        if not alimento:
            db.rollback()
            return jsonify({'erro': "Alimento do pedido não encontrado no estoque"}), 404
        if alimento.quantidade < pedido.quantidade_pedido:
            db.rollback()
            return jsonify(
                {'erro': f"Estoque insuficiente para {alimento.nome}. Disponível: {alimento.quantidade}"}), 400

        # 1. Baixa no estoque
        alimento.quantidade -= pedido.quantidade_pedido
        # 2. Atualiza o status do pedido
        pedido.status_pagamento = 'pago'
        # Commit da transação (pedido e estoque)
        db.commit()

        return jsonify({
            'msg': 'Pedido pago e estoque atualizado com sucesso!',
            'id_pedido': pedido.id_pedido,
            'metodo_pagamento': metodo,
            'status_novo': 'pago'
        }), 200

    except Exception as e:
        db.rollback()
        logging.error(f"Erro ao finalizar pedido: {e}")
        return jsonify({'erro': "Erro interno ao finalizar pedido"}), 500

    finally:
        db.close()


if __name__ == '__main__':
    print("Iniciando a API...")
    app.run(debug=True, host='0.0.0.0', port=5001)