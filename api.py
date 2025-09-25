import sqlalchemy
from flask import Flask, jsonify, request
from flask_jwt_extended import get_jwt_identity, JWTManager, create_access_token, jwt_required
from functools import wraps
from sqlalchemy import select
from models import Usuario, Alimento, Pedido, local_session

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super_senha"
jwt = JWTManager(app)

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

# Rota de boas-vindas
@app.route('/')
def index():
    return jsonify({'message': 'Welcome to Exemplo API!'})

# Login
@app.route('/login', methods=['POST'])
def login():
    dados = request.get_json()
    email = dados.get('email')
    senha = dados.get('senha')

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

# Listar alunos e funcionários (todos os usuários)
@app.route('/alunos', methods=['GET'])
# @jwt_required()
def lista_pessoa():
    banco = local_session()
    try:
        sql = select(Usuario)
        tds_usuarios = banco.execute(sql).scalars()
        lista_usuarios = [usuario.serialize_usuario() for usuario in tds_usuarios]
        # Remove senha_hash do retorno por segurança
        for u in lista_usuarios:
            if 'senha_hash' in u:
                del u['senha_hash']
        return jsonify({"usuarios": lista_usuarios}), 200
    except Exception as e:
        return jsonify({"msg": f"Erro ao listar usuário: {str(e)}"}), 500
    finally:
        banco.close()

# Listar alimentos (qualquer um pode acessar)
@app.route('/alimento', methods=['GET'])
def get_alimento():
    db_session = local_session()
    try:
        sql_alimento = select(Alimento)
        resultado_alimento = db_session.execute(sql_alimento).scalars()
        lista_alimento = []
        for alimento in resultado_alimento:
            alimento_data = alimento.serialize_alimento()
            alimento_data["id_alimento"] = alimento.id_alimento
            lista_alimento.append(alimento_data)
        return jsonify({'alimento': lista_alimento}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        db_session.close()

@app.route('/usuarios', methods=['POST'])
# @jwt_required()
# @admin_required
def cadastro_usuarios():
    dados = request.get_json()
    nome = dados.get('nome')
    cpf = dados.get('cpf')
    email = dados.get('email')
    papel = dados.get('papel', 'aluno')
    senha = dados.get('senha_hash')

    if not nome or not email or not senha:
        return jsonify({"msg": "Nome, email e senha são obrigatórios"}), 400

    banco = local_session()
    try:
        # Verifica se já existe usuário com o email
        user_check = select(Usuario).where(Usuario.email == email)
        usuario_existente = banco.execute(user_check).scalar()
        if usuario_existente:
            return jsonify({"msg": "Usuário já existe"}), 400

        novo_usuario = Usuario(nome=nome, cpf=cpf, email=email, papel=papel)
        novo_usuario.set_senha_hash(senha)
        banco.add(novo_usuario)
        banco.commit()

        return jsonify({"msg": "Usuário criado com sucesso", "user_id": novo_usuario.id_usuario}), 201
    except Exception as e:
        banco.rollback()
        return jsonify({"msg": f"Erro ao registrar usuário: {str(e)}"}), 500
    finally:
        banco.close()

# Cadastrar alimento (somente funcionário)
@app.route('/novo_alimento', methods=['POST'])
# @jwt_required()
# @admin_required
def cadastrar_alimento():
    dados = request.get_json()
    db_session = local_session()
    try:
        required_fields = ['nome', 'valor', 'quantidade', 'marca', 'categoria', 'descricao']
        if not all(dados.get(field) for field in required_fields):
            return jsonify({'erro': "Todos os campos são obrigatórios"}), 400

        categoria = dados['categoria'].lower()
        if categoria not in ['bebida', 'doce', 'salgado']:
            return jsonify({'erro': "Categoria inválida. Use: bebida, doce ou salgado"}), 400

        novo_alimento = Alimento(
            nome=dados['nome'],
            valor=dados['valor'],
            quantidade=dados['quantidade'],
            categoria=categoria,
            descricao=dados['descricao'],
            marca=dados['marca']
        )
        novo_alimento.save(db_session)
        alimento_response = novo_alimento.serialize_alimento()
        alimento_response["id_alimento"] = novo_alimento.id_alimento
        return jsonify(alimento_response), 201
    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db_session.close()

@app.route('/editar_usuario/<int:id>', methods=['PUT', 'POST'])
# @jwt_required()
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
            # Remove senha_hash do retorno
            if 'senha_hash' in usuario_response:
                del usuario_response['senha_hash']
            return jsonify(usuario_response), 200
        return jsonify({"msg": "Nenhuma alteração realizada"}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'erro': str(e)}), 400
    finally:
        db_session.close()

# Editar alimento (somente funcionário)
@app.route('/editar_alimento/<int:id>', methods=['PUT', 'POST'])
# @jwt_required()
# @admin_required
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

# Listar pedidos (qualquer um pode consultar)
@app.route('/pedido', methods=['GET'])
def get_pedido():
    db_session = local_session()
    try:
        sql_pedido = select(Pedido)
        resultado_pedido = db_session.execute(sql_pedido).scalars()
        lista_pedido = []
        for pedido in resultado_pedido:
            pedido_data = pedido.serialize_pedido()
            pedido_data["id_pedido"] = pedido.id_pedido
            lista_pedido.append(pedido_data)
        return jsonify({'pedido': lista_pedido}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    finally:
        db_session.close()

# Cadastrar pedido (qualquer usuário pode criar pedido)
@app.route('/novo_pedido', methods=['POST'])
def cadastrar_pedido():
    dados = request.get_json()
    db_session = local_session()
    try:
        required_fields = ['nome_aluno', 'nome_pedido', 'valor_pedido', 'quantidade_pedido']
        if not all(dados.get(field) for field in required_fields):
            return jsonify({'erro': "Todos os campos são obrigatórios"}), 400

        novo_pedido = Pedido(
            nome_aluno=dados['nome_aluno'],
            nome_pedido=dados['nome_pedido'],
            valor_pedido=dados['valor_pedido'],
            quantidade_pedido=dados['quantidade_pedido']
        )
        novo_pedido.save(db_session)
        pedido_response = novo_pedido.serialize_pedido()
        pedido_response["id_pedido"] = novo_pedido.id_pedido
        return jsonify(pedido_response), 201
    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db_session.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
