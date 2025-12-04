import logging
from functools import wraps
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import get_jwt_identity, JWTManager, create_access_token, jwt_required
from flask_pydantic_spec import FlaskPydanticSpec
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload

from models import Usuario, Alimento, Pedido, local_session

from sqlalchemy import func, desc


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super_senha"
app.config['JWT_SECRET_KEY'] = 'super_senha'
jwt = JWTManager(app)
CORS(app)
spec = FlaskPydanticSpec('flask', title='API - AROMA & SABOR', version='1.0.0')


def admin_required(fn):
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
    """
    API para autenticar um usuário e gerar um token de acesso JWT.
    {
        "email": "email_do_usuario",
        "senha": "senha_do_usuario"
    }
    """

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
@jwt_required()
@admin_required
def lista_usuarios():
    """
    API para listar todos os usuários cadastrados.

    Retorna:
    {
        "usuarios": [
            {
                "email": "usuario1@exemplo.com",
                "id_usuario": 1,
                "nome": "Usuário Um",
                "papel": "aluno" / funcionario
            }
        ]
    }
    """
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
    """
    API para cadastrar um novo usuário no sistema.

    {
        "nome": "Novo Usuário",
        "email": "novo@aluno",
        "senha": "senha",
        "papel": "aluno"
    }

    Retorna (Sucesso - 201):
    {
        "msg": "Usuário criado com sucesso",
        "user_id": 10
    }
    """

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
@admin_required
def editar_usuario(id):
    """
    API para editar os dados de um usuário pelo ID.

    (Campos Opcionais):
    {
        "nome": "novo nome",
        "email": "novo_email@exemplo.com",
        "senha": "nova_senha"
    }

    Retorna (Sucesso - 200):
    {
        "email": "novo_email@exemplo.com",
        "id_usuario": 1,
        "nome": "Nome Atualizado",
        "papel": "aluno"
    }
    """
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
    """
    API para listar todos os alimentos (produtos) disponíveis.

    {
        "alimento": [
            {
                "categoria": "doce",
                "descricao": "Chocolate ao leite",
                "id_alimento": 1,
                "marca": "Choc",
                "nome": "Chocolate",
                "quantidade": 50,
                "valor": 5.5
            }
        ]
    }
    """

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
    """
    API para adicionar um novo alimento ao estoque. Requer que seja funcionário.

    {
        "nome": "Refrigerante Coca",
        "valor": 7.00,
        "quantidade": 100,
        "marca": "Refri",
        "categoria": "bebida",
        "descricao": "Lata de 350ml"
    }

    Sucesso - 201:
    {
        "categoria": "bebida",
        "descricao": "Lata de 350ml",
        "id_alimento": 5,
        "marca": "Refri",
        "nome": "Refrigerante Coca",
        "quantidade": 100,
        "valor": 7.0
    }
    """

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
    """
    API para editar os dados de um alimento pelo ID. Requer que seja funcionário.
    {
        "quantidade": 80,
        "valor": 7.50,
        "categoria": "doce"
    }

    Retorna (Sucesso - 200):
    {
        "categoria": "doce",
        "descricao": "Chocolate ao leite",
        "id_alimento": 1,
        "marca": "Choc",
        "nome": "Chocolate",
        "quantidade": 80,
        "valor": 7.5
    }
    """
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
    """
    API para listar todos os pedidos realizados.

    {
        "pedidos": [
            {
                "id_alimento": 1,
                "id_pedido": 1,
                "nome_aluno": "Aluno",
                "nome_pedido": "Chocolate",
                "quantidade_pedido": 2,
                "status_pagamento": "pendente",
                "valor_pedido": 5.5
            }
        ]
    }
    """
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
    """
    API para criar um ou mais pedidos, validando estoque e registrando o aluno.

    {
        "nome_aluno": "Gabriele",
        "pedidos": [
            {
                "nome": "Chocolate",
                "valor": 5.5,
                "quantidade": 1
            }
        ]
    }

    Sucesso - 201:
    {
        "msg": "Pedidos cadastrados com sucesso",
        "pedidos": [
            {
                "id_alimento": 1,
                "id_pedido": 20,
                "nome_aluno": "Gabriele",
                "nome_pedido": "Chocolate",
                "quantidade_pedido": 1,
                "status_pagamento": "pendente",
                "valor_pedido": 5.5
            }
        ]
    }
    """
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
def finalizar_pedido(id_pedido):
    """
    API para marcar um pedido como pago e dar baixa no estoque.

    {
        "metodo_pagamento": "pix" // Opções: 'pix', 'dinheiro', 'cartao'
    }

    Sucesso - 200:
    {
        "msg": "Pedido pago e estoque atualizado com sucesso!",
        "id_pedido": 1,
        "metodo_pagamento": "pix",
        "status_novo": "pago"
    }
    """
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

# para fazer o grafico naaplicação web
@app.route('/produtos_mais_vendidos', methods=["GET"])
@jwt_required()
@admin_required
def grafico_produtos_mais_vendidos():
    """
    API para listar os 5 produtos mais vendidos.

    Retorna:
    {
        "produtos_mais_vendidos": [
            {
                "nome": "Produto A",
                "quantidade": 50,
                "valor": 10.0,
                "lucro": 500.0
            }
        ]
    }
    """
    db = local_session()
    try:
        resultado = (
            db.query(
                Pedido.id_alimento,
                Alimento.nome,
                Alimento.valor,
                func.sum(Pedido.quantidade_pedido).label("quantidade_total")
            )
            .join(Alimento, Pedido.id_alimento == Alimento.id_alimento)
            .group_by(Pedido.id_alimento)
            .order_by(desc("quantidade_total"))
            .limit(5)  #os 5 mais vendidos
            .all()
        )

        produtos = []
        for item in resultado:
            produtos.append({
                "nome": item.nome,
                "quantidade": int(item.quantidade_total),
                "valor": float(item.valor),
                "lucro": float(item.valor * item.quantidade_total)
            })

        return jsonify({"produtos_mais_vendidos": produtos}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"erro": str(e)}), 500

    finally:
        db.close()


if __name__ == '__main__':
    print("Iniciando a API...")
    app.run(debug=True, host='0.0.0.0', port=5001)