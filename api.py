import sqlalchemy
from flask import Flask, jsonify, request
from flask_jwt_extended import get_jwt_identity, JWTManager, create_access_token, jwt_required
from functools import wraps
from sqlalchemy import select
from models import Usuario, Alimento, Pedido, local_session, init_db

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super_senha"
jwt = JWTManager(app)
init_db()

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        db = local_session()
        try:
            sql = select(Usuario).where(Usuario.email == current_user)
            user = db.execute(sql).scalar()
            if user and user.papel == "funcionario":
                return fn(*args, **kwargs)
            return jsonify(msg="Acesso negado: Requer privilégios de administrador"), 403
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
        sql = select(Usuario).where(Usuario.email == email)
        user = db.execute(sql).scalar()
        if user and user.check_password(senha):
            access_token = create_access_token(identity=str(user.email))
            return jsonify({
                "access_token": access_token,
                "papel": user.papel,
            }), 200
        return jsonify({"msg": "Credenciais inválidas"}), 401
    except Exception as e:
        return jsonify({"msg": str(e)}), 500
    finally:
        db.close()

@app.route('/alunos', methods=['GET'])
def lista_pessoa():
    banco = local_session()
    try:
        sql = select(Usuario)
        tds_usuarios = banco.execute(sql).scalars()
        lista_usuarios = [usuario.serialize_usuario() for usuario in tds_usuarios]
        return jsonify({"usuarios": lista_usuarios}), 200
    except Exception as e:
        return jsonify({"msg": f"Erro ao listar usuário: {str(e)}"}), 500
    finally:
        banco.close()


import logging

logging.basicConfig(level=logging.DEBUG)


@app.route('/usuarios', methods=['POST'])
def cadastro_usuarios():
    dados = request.get_json()

    nome = dados.get('nome')
    email = dados.get('email')
    papel = dados.get('papel', 'aluno')
    senha = dados.get('senha')
    cpf = 'none'

    if not nome or not email or not senha:
        return jsonify({"msg": "Nome, email e senha são obrigatórios"}), 400
    if papel == "aluno" and not email.endswith("@aluno"):
        return jsonify({"msg": "Email de aluno deve terminar com '@aluno'"}), 400

    logging.debug(f"Recebido cadastro de usuário: {dados}")

    banco = local_session()
    try:
        if banco.execute(select(Usuario).where(Usuario.email == email)).scalar():
            return jsonify({"msg": "Usuário com esse email já existe"}), 400
        if cpf and banco.execute(select(Usuario).where(Usuario.cpf == cpf)).scalar():
            return jsonify({"msg": "Usuário com esse CPF já existe"}), 400

        novo_usuario = Usuario(nome=nome, email=email, papel=papel, cpf=cpf)
        novo_usuario.set_senha_hash(senha)
        banco.add(novo_usuario)
        banco.commit()

        logging.debug(f"Usuário {nome} registrado com sucesso!")

        return jsonify({
            "msg": "Usuário criado com sucesso",
            "user_id": novo_usuario.id_usuario
        }), 201
    except Exception as e:
        banco.rollback()
        logging.error(f"Erro ao registrar usuário: {str(e)}")
        return jsonify({"msg": f"Erro ao registrar usuário: {str(e)}"}), 500
    finally:
        banco.close()


# @app.route('/usuarios', methods=['POST'])
# def cadastro_usuarios():
#     dados = request.get_json()
#     nome = dados.get('nome')
#     email = dados.get('email')
#     papel = dados.get('papel', 'aluno')
#     senha = dados.get('senha')
#     cpf = dados.get('cpf', None)
#
#     if not nome or not email or not senha:
#         return jsonify({"msg": "Nome, email e senha são obrigatórios"}), 400
#
#     if papel == "aluno" and not email.endswith("@aluno"):
#         return jsonify({"msg": "Email de aluno deve terminar com '@aluno'"}), 400
#
#     banco = local_session()
#     try:
#         if banco.execute(select(Usuario).where(Usuario.email == email)).scalar():
#             return jsonify({"msg": "Usuário com esse email já existe"}), 400
#         if cpf and banco.execute(select(Usuario).where(Usuario.cpf == cpf)).scalar():
#             return jsonify({"msg": "Usuário com esse CPF já existe"}), 400
#
#         novo_usuario = Usuario(nome=nome, email=email, papel=papel, cpf=cpf)
#         novo_usuario.set_senha_hash(senha)
#         banco.add(novo_usuario)
#         banco.commit()
#         return jsonify({"msg": "Usuário criado com sucesso", "user_id": novo_usuario.id_usuario}), 201
#     # except Exception as e:
#     #     banco.rollback()
#     #     return jsonify({"msg": f"Erro ao registrar usuário: {str(e)}"}), 500
#     except Exception as e:
#         banco.rollback()
#         print(f"Erro ao registrar usuário: {str(e)}")  # Para debugar
#         return jsonify({"msg": f"Erro ao registrar usuário: {str(e)}"}), 500
#     finally:
#         banco.close()


# @app.route('/usuarios', methods=['POST'])
# def cadastro_usuarios():
#     dados = request.get_json()
#     nome = dados.get('nome')
#     email = dados.get('email')
#     papel = dados.get('papel', 'aluno')
#     senha = dados.get('senha')
#     cpf = dados.get('cpf', None)
#
#     if not nome or not email or not senha:
#         return jsonify({"msg": "Nome, email e senha são obrigatórios"}), 400
#
#     if not email.endswith("@aluno"):
#         return jsonify({"msg": "Email deve terminar com '@aluno'"}), 400
#
#     banco = local_session()
#     try:
#         if banco.execute(select(Usuario).where(Usuario.email == email)).scalar():
#             return jsonify({"msg": "Usuário com esse email já existe"}), 400
#         if cpf and banco.execute(select(Usuario).where(Usuario.cpf == cpf)).scalar():
#             return jsonify({"msg": "Usuário com esse CPF já existe"}), 400
#
#         novo_usuario = Usuario(nome=nome, email=email, papel=papel, cpf=cpf)
#         novo_usuario.set_senha_hash(senha)
#         banco.add(novo_usuario)
#         banco.commit()
#         return jsonify({"msg": "Usuário criado com sucesso", "user_id": novo_usuario.id_usuario}), 201
#     except Exception as e:
#         banco.rollback()
#         return jsonify({"msg": f"Erro ao registrar usuário: {str(e)}"}), 500
#     finally:
#         banco.close()

@app.route('/alimento', methods=['GET'])
def get_alimento():
    db_session = local_session()
    try:
        sql_alimento = select(Alimento)
        resultado_alimento = db_session.execute(sql_alimento).scalars()
        lista_alimento = []
        for alimento in resultado_alimento:
            lista_alimento.append(alimento.serialize_alimento())
        return jsonify({'alimento': lista_alimento}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        db_session.close()

@app.route('/novo_alimento', methods=['POST'])
# @jwt_required()
# @admin_required
def cadastrar_alimento():
    dados = request.get_json()
    db_session = local_session()
    try:
        campos = ['nome', 'valor', 'quantidade', 'marca', 'categoria', 'descricao']
        if not all(dados.get(c) is not None for c in campos):
            return jsonify({'erro': "Todos os campos são obrigatórios"}), 400

        categoria = dados['categoria'].lower()
        if categoria not in ['bebida', 'doce', 'salgado']:
            return jsonify({'erro': "Categoria inválida. Use: bebida, doce ou salgado"}), 400

        novo = Alimento(
            nome=dados['nome'],
            valor=float(dados['valor']),
            quantidade=int(dados['quantidade']),
            categoria=categoria,
            descricao=dados['descricao'],
            marca=dados['marca']
        )
        novo.save(db_session)
        retorno = novo.serialize_alimento()
        retorno["id_alimento"] = novo.id_alimento
        return jsonify(retorno), 201
    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db_session.close()

@app.route('/pedido', methods=['GET'])
def get_pedido():
    db_session = local_session()
    try:
        sql_pedido = select(Pedido)
        resultado = db_session.execute(sql_pedido).scalars()
        lista = [p.serialize_pedido() for p in resultado]
        return jsonify({'pedido': lista}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        db_session.close()

@app.route('/novo_pedido', methods=['POST'])
def cadastrar_pedido():
    dados = request.get_json()
    db_session = local_session()
    try:
        pedidos = dados.get("pedidos")
        nome_aluno = dados.get("nome_aluno")

        if not pedidos or not nome_aluno:
            return jsonify({'erro': "Dados incompletos"}), 400

        for item in pedidos:
            if not all(k in item for k in ['nome', 'valor', 'quantidade']):
                return jsonify({'erro': "Cada item precisa de nome, valor e quantidade"}), 400

            # Buscar o id_alimento pelo nome do alimento
            alimento = db_session.execute(select(Alimento).where(Alimento.nome == item['nome'])).scalar()
            if not alimento:
                return jsonify({'erro': f'Alimento {item["nome"]} não encontrado'}), 404

            novo = Pedido(
                nome_aluno=nome_aluno,
                nome_pedido=item['nome'],
                valor_pedido=float(item['valor']),
                quantidade_pedido=int(item['quantidade']),
                id_alimento=alimento.id_alimento
            )
            db_session.add(novo)

        db_session.commit()
        return jsonify({'msg': 'Pedidos cadastrados com sucesso'}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db_session.close()

@app.route('/finalizar_pedido/<int:id_pedido>', methods=['POST'])
def finalizar_pedido(id_pedido):
    dados = request.get_json()
    metodo = dados.get('metodo_pagamento')
    if metodo is None:
        return jsonify({'erro': "Método de pagamento deve ser informado"}), 400

    metodo = metodo.lower()
    if metodo not in ['pix', 'dinheiro']:
        return jsonify({'erro': "Método de pagamento inválido"}), 400

    db_session = local_session()
    try:
        pedido = db_session.query(Pedido).filter(Pedido.id_pedido == id_pedido).first()
        if not pedido:
            return jsonify({'erro': "Pedido não encontrado"}), 404

        pedido.status_pagamento = 'pago'
        db_session.commit()

        return jsonify({
            'msg': 'Pedido pago com sucesso!',
            'id_pedido': pedido.id_pedido
        }), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'erro': str(e)}), 500
    finally:
        db_session.close()

@app.route('/editar_usuario/<int:id>', methods=['PUT', 'POST'])
def editar_usuario(id):
    dados = request.get_json()
    db_session = local_session()
    try:
        usuario = db_session.execute(select(Usuario).where(Usuario.id_usuario == id)).scalar()
        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404

        updated = False
        if 'nome' in dados and dados['nome'] is not None:
            usuario.nome = dados['nome']
            updated = True
        if 'cpf' in dados and dados['cpf'] is not None:
            usuario.cpf = dados['cpf']
            updated = True
        if 'email' in dados and dados['email'] is not None:
            usuario.email = dados['email']
            updated = True
        if 'papel' in dados and dados['papel'] is not None:
            usuario.papel = dados['papel']
            updated = True
        if 'senha_hash' in dados and dados['senha_hash'] is not None:
            usuario.set_senha_hash(dados['senha_hash'])
            updated = True

        if updated:
            db_session.add(usuario)
            db_session.commit()
            usuario_response = usuario.serialize_usuario()
            if 'senha_hash' in usuario_response:
                del usuario_response['senha_hash']
            return jsonify(usuario_response), 200
        return jsonify({"msg": "Nenhuma alteração realizada"}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db_session.close()

@app.route('/editar_alimento/<int:id>', methods=['PUT', 'POST'])
@jwt_required()
@admin_required
def editar_alimento(id):
    dados = request.get_json()
    db_session = local_session()
    try:
        alimento = db_session.execute(select(Alimento).where(Alimento.id_alimento == id)).scalar()
        if not alimento:
            return jsonify({'erro': 'Alimento não encontrado'}), 404

        updated = False
        if 'nome' in dados and dados['nome'] is not None:
            alimento.nome = dados['nome']
            updated = True
        if 'valor' in dados and dados['valor'] is not None:
            alimento.valor = dados['valor']
            updated = True
        if 'quantidade' in dados and dados['quantidade'] is not None:
            alimento.quantidade = dados['quantidade']
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
            alimento.save(db_session)
            alimento_response = alimento.serialize_alimento()
            alimento_response["id_alimento"] = alimento.id_alimento
            return jsonify(alimento_response), 200
        return jsonify({"msg": "Nenhuma alteração realizada"}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db_session.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
