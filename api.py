import sqlalchemy
from dateutil.relativedelta import relativedelta
from flask import Flask, jsonify, redirect, request
from flask_pydantic_spec import FlaskPydanticSpec, spec
from datetime import date, datetime, timedelta
from functools import wraps
from models import Funcionario, Aluno, Salgado, Doce, Bebida, Pedido, local_session
from datetime import date
# from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from flask_jwt_extended import get_jwt_identity, JWTManager, create_access_token, jwt_required
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super_senha"
jwt = JWTManager(app)
db_session = local_session()

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        print(f'c_user:{current_user}')
        db = local_session()
        try:
            sql = select(Funcionario).where(Funcionario.email_funcionario == current_user)
            user = db.execute(sql).scalar()
            print(f'teste admin: {user and user.papel == "funcionario"} {user.papel}')
            if user and user.papel == "funcionario":
                return fn(*args, **kwargs)
            return jsonify(msg="Acesso negado: Requer privilégios de administrador"), 403
        finally:
            db.close()
    return wrapper

#Rota de login
@app.route('/')
def index():
    return jsonify({
        'message': 'Welcome to Exemplo API!',
    })

@app.route('/login', methods=['POST'])
def login():
    dados = request.get_json()
    email = dados['email']
    senha = dados['senha']

    db = local_session()

    try:
        sql = select(Funcionario).where(Funcionario.email_funcionario == email)
        user = db.execute(sql).scalar()

        if user and user.check_password(senha):
            print("if login")
            access_token = create_access_token(identity=str(user.email))
            return jsonify({
                "access_token":access_token,
                "papel": user.papel,
            }), 200
        return jsonify({"msg": "Credenciais inválidas"}), 401
    except Exception as e:
        print(e)
        return jsonify({"msg": str(e)}), 500
    finally:
        db.close()

#GETS:
#GET ALUNO

@app.route('/alunos', methods=['GET'])
def get_alunos():
    try:
        sql_alunos = select(Aluno)
        resultado_alunos = db_session.execute(sql_alunos).scalars()
        lista_alunos = []
        for aluno in resultado_alunos:
            aluno_data = aluno.serialize_aluno()
            aluno_data["id_aluno"] = aluno.id_aluno
            lista_alunos.append(aluno_data)
        return jsonify({'alunos': lista_alunos}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/funcionarios', methods=['GET'])
def get_funcionarios():
    try:
        sql_funcionario = select(Funcionario)
        resultado_funcionario = db_session.execute(sql_funcionario).scalars()
        lista_funcionario = []
        for funcionario in resultado_funcionario:
            funcionario_data = funcionario.serialize_funcionario()
            funcionario_data["id"] = funcionario.id
            lista_funcionario.append(funcionario_data)
        return jsonify({'funcionarios': lista_funcionario}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/salgados', methods=['GET'])
def get_salgados():
    try:
        sql_salgado = select(Salgado)
        resultado_salgado = db_session.execute(sql_salgado).scalars()
        lista_salgado = []
        for salgado in resultado_salgado:
            salgado_data = salgado.serialize_salgado()
            salgado_data["id_salgado"] = salgado.id_salgado
            lista_salgado.append(salgado_data)
        return jsonify({'funcionarios': lista_salgado}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/doces', methods=['GET'])
def get_doces():
    try:
        sql_doce = select(Doce)
        resultado_doce = db_session.execute(sql_doce).scalars()
        lista_doce = []
        for doce in resultado_doce:
            doce_data = doce.serialize_doce()
            doce_data["id_doce"] = doce.id_doce
            lista_doce.append(doce_data)
        return jsonify({'funcionarios': lista_doce}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/bebidas', methods=['GET'])
def get_bebidas():
    try:
        sql_bebida = select(Bebida)
        resultado_bebida = db_session.execute(sql_bebida).scalars()
        lista_bebida = []
        for bebida in resultado_bebida:
            bebida_data = bebida.serialize_bebida()
            bebida_data["id_bebida"] = bebida.id_bebida
            lista_bebida.append(bebida_data)
        return jsonify({'bebidas': lista_bebida}), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


#POST
@app.route('/novo_aluno', methods=['POST'])
def cadastrar_aluno():

    dados = request.get_json()
    db_session = local_session()
    try:
        cpf_value = dados.get('cpf') or dados.get('cpf')
        if not all([dados.get('nome'), dados.get('email'), dados.get('papel'), dados.get('senha_hash')]):
            return jsonify({'erro': "Campos obrigatórios (nome, cpf, email) não podem ser vazios"}), 400

        novo_aluno = Aluno(
            nome=dados['nome'],
            cpf=cpf_value,
            email=dados['email'],
            papel=dados['papel'],
            senha_hash=dados['senha_hash'],
        )
        # novo_aluno.save(db_session)
        db_session.add(novo_aluno)
        db_session.commit()
        aluno_response = novo_aluno.serialize_aluno()
        aluno_response["id_aluno"] = novo_aluno.id_aluno
        return jsonify(aluno_response), 201
    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db_session.close()


@app.route('/novo_funcionario', methods=['POST'])
def cadastrar_funcionario():

    dados = request.get_json()
    db_session = local_session()
    try:
        if not all([dados.get('nome_funcionario'), dados.get('email_funcionario'), dados.get('papel_funcionario'),
                    dados.get('senha_hash_funcionario')]):
            return jsonify({'erro': "Campos obrigatórios (nome, email) não podem ser vazios"}), 400

        novo_funcionario = Funcionario(
            nome_funcionario =dados['nome_funcionario'],
            email_funcionario=dados['email_funcionario'],
            papel_funcionario=dados['papel_funcionario'],
            senha_hash_funcionario=dados['senha_hash_funcionario'],
        )
        # novo_funcionario.save(db_session)
        db_session.add(novo_funcionario)
        db_session.commit()
        funcionario_response = novo_funcionario.serialize_funcionario()
        funcionario_response["id"] = novo_funcionario.id
        return jsonify(funcionario_response), 201
    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db_session.close()


@app.route('/novo_salgado', methods=['POST'])
# @admin_required
# @jwt_required
def cadastrar_salgado():

    dados = request.get_json()
    db_session = local_session()
    try:
        if not all([dados.get('nome_salgado'), dados.get('valor_salgado'), dados.get('quantidade_salgado')]):
            return jsonify({'erro': "Campos obrigatórios (nome, valor, quantidade) não podem ser vazios"}), 400

        novo_salgado = Salgado(
            nome_salgado =dados['nome_salgado'],
            valor_salgado =dados['valor_salgado'],
            quantidade_salgado =dados['quantidade_salgado'],
        )
        novo_salgado.save(db_session)
        salgado_response = novo_salgado.serialize_salgado()
        salgado_response["id_salgado"] = novo_salgado.id_salgado
        return jsonify(salgado_response), 201
    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db_session.close()


@app.route('/novo_doce', methods=['POST'])
def cadastrar_doce():

    dados = request.get_json()
    db_session = local_session()
    try:
        if not all([dados.get('nome_doce'), dados.get('valor_doce'), dados.get('quantidade_doce')]):
            return jsonify({'erro': "Campos obrigatórios (nome, valor, quantidade) não podem ser vazios"}), 400

        novo_doce = Doce(
            nome_doce =dados['nome_doce'],
            valor_doce =dados['valor_doce'],
            quantidade_doce =dados['quantidade_doce'],
        )
        novo_doce.save(db_session)
        doce_response = novo_doce.serialize_doce()
        doce_response["id_doce"] = novo_doce.id_doce
        return jsonify(doce_response), 201
    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db_session.close()


@app.route('/novo_bebida', methods=['POST'])
def cadastrar_bebida():

    dados = request.get_json()
    db_session = local_session()
    try:
        if not all([dados.get('nome_bebida'), dados.get('valor_bebida'), dados.get('quantidade_bebida')]):
            return jsonify({'erro': "Campos obrigatórios (nome, valor, quantidade) não podem ser vazios"}), 400

        novo_bebida = Bebida(
            nome_bebida =dados['nome_bebida'],
            valor_bebida =dados['valor_bebida'],
            quantidade_bebida =dados['quantidade_bebida'],
        )
        novo_bebida.save(db_session)
        bebida_response = novo_bebida.serialize_bebida()
        bebida_response["id_bebida"] = novo_bebida.id_bebida
        return jsonify(bebida_response), 201
    except Exception as e:
        return jsonify({'erro': str(e)}), 400
    finally:
        db_session.close()



#EDITAR
@app.route('/editar_aluno/<id>', methods=['PUT', 'POST'])
def editar_aluno(id):

    dados = request.get_json()
    try:
        aluno = db_session.execute(select(Aluno).where(Aluno.id_aluno == id)).scalar()
        if not aluno:
            return jsonify({'erro': 'Usuário não encontrado'}), 404

        updated = False
        if 'nome_aluno' in dados and dados['nome_aluno'] is not None:
            aluno.nome_aluno = dados['nome_aluno']
            updated = True
        if 'cpf' in dados and dados['cpf'] is not None:
            aluno.cpf = dados['cpf']
            updated = True
        if 'email' in dados and dados['email'] is not None:
            aluno.email = dados['email']
            updated = True
        if 'papel' in dados and dados['papel'] is not None:
            aluno.papel = dados['papel']
            updated = True
        if 'senha_hash' in dados and dados['senha_hash'] is not None:
            aluno.senha_hash = dados['senha_hash']
            updated = True

        if updated:
            # aluno.save()
            db_session.add(aluno)
            db_session.commit()
            aluno_response = aluno.serialize_aluno()
            aluno_response["id_aluno"] = aluno.id_aluno
            return jsonify(aluno_response)
    except Exception as e:
        return jsonify({'erro': str(e)}), 400

@app.route('/editar_funcionario/<id>', methods=['PUT', 'POST'])
def editar_funcionario(id):

    dados = request.get_json()
    try:
        funcionario = db_session.execute(select(Funcionario).where(Funcionario.id == id)).scalar()
        if not funcionario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404

        updated = False
        if 'nome_funcionario' in dados and dados['nome_funcionario'] is not None:
            funcionario.nome_funcionario = dados['nome_funcionario']
            updated = True
        if 'email_funcionario' in dados and dados['email_funcionario'] is not None:
            funcionario.email_funcionario = dados['email_funcionario']
            updated = True
        if 'papel_funcionario' in dados and dados['papel_funcionario'] is not None:
            funcionario.papel_funcionario = dados['papel_funcionario']
        if 'senha_hash_funcionario' in dados and dados['senha_hash_funcionario'] is not None:
            funcionario.senha_hash_funcionario = dados['senha_hash_funcionario']
            updated = True

        if updated:
            # funcionario.save()
            db_session.add(funcionario)
            db_session.commit()
            funcionario_response = funcionario.serialize_funcionario()
            funcionario_response["id_aluno"] = funcionario.id
            return jsonify(funcionario_response)
    except Exception as e:
        return jsonify({'erro': str(e)}), 400

@app.route('/editar_salgado/<id>', methods=['PUT', 'POST'])
def editar_salgado(id):

    dados = request.get_json()
    try:
        salgado = db_session.execute(select(Salgado).where(Salgado.id_salgado == id)).scalar()
        if not salgado:
            return jsonify({'erro': 'Salgado não encontrado'}), 404

        updated = False
        if 'nome_salgado' in dados and dados['nome_salgado'] is not None:
            salgado.nome_salgado = dados['nome_salgado']
            updated = True
        if 'valor_salgado' in dados and dados['valor_salgado'] is not None:
            salgado.valor_salgado = dados['valor_salgado']
            updated = True
        if 'quantidade_salgado' in dados and dados['quantidade_salgado'] is not None:
            salgado.quantidade_salgado = dados['quantidade_salgado']

        if updated:
            salgado.save(db_session)
            salgado_response = salgado.serialize_salgado()
            salgado_response["id_salgado"] = salgado.id_salgado
            return jsonify(salgado_response)
    except Exception as e:
        return jsonify({'erro': str(e)}), 400


@app.route('/editar_doce/<id>', methods=['PUT', 'POST'])
def editar_doce(id):

    dados = request.get_json()
    try:
        doce = db_session.execute(select(Doce).where(Doce.id_doce == id)).scalar()
        if not doce:
            return jsonify({'erro': 'Doce não encontrado'}), 404

        updated = False
        if 'nome_doce' in dados and dados['nome_doce'] is not None:
            doce.nome_doce = dados['nome_doce']
            updated = True
        if 'valor_doce' in dados and dados['valor_doce'] is not None:
            doce.valor_doce = dados['valor_doce']
            updated = True
        if 'quantidade_doce' in dados and dados['quantidade_doce'] is not None:
            doce.quantidade_doce = dados['quantidade_doce']

        if updated:
            doce.save(db_session)
            doce_response = doce.serialize_doce()
            doce_response["id_doce"] = doce.id_doce
            return jsonify(doce_response)
    except Exception as e:
        return jsonify({'erro': str(e)}), 400

@app.route('/editar_bebida/<id>', methods=['PUT', 'POST'])
def editar_bebida(id):

    dados = request.get_json()
    try:
        bebida = db_session.execute(select(Bebida).where(Bebida.id_bebida == id)).scalar()
        if not bebida:
            return jsonify({'erro': 'Bebida não encontrado'}), 404

        updated = False
        if 'nome_bebida' in dados and dados['nome_bebida'] is not None:
            bebida.nome_bebida = dados['nome_bebida']
            updated = True
        if 'valor_bebida' in dados and dados['valor_bebida'] is not None:
            bebida.valor_bebida = dados['valor_bebida']
            updated = True
        if 'quantidade_bebida' in dados and dados['quantidade_bebida'] is not None:
            bebida.quantidade_bebida = dados['quantidade_bebida']

        if updated:
            bebida.save(db_session)
            bebida_response = bebida.serialize_bebida()
            bebida_response["id_bebida"] = bebida.id_bebida
            return jsonify(bebida_response)
    except Exception as e:
        return jsonify({'erro': str(e)}), 400


#PEDIDO
@app.route('/pedido', methods=['GET'])
def get_pedido():
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

@app.route('/novo_pedido', methods=['POST'])
def cadastrar_pedido():

    dados = request.get_json()
    db_session = local_session()
    try:
        if not all([dados.get('nome_aluno'), dados.get('nome_pedido'), dados.get('valor_pedido'),
                    dados.get('quantidade_pedido')]):
            return jsonify({'erro': "Campos obrigatórios (nome, valor, quantidade) não podem ser vazios"}), 400

        novo_pedido = Pedido(
            nome_aluno =dados['nome_aluno'],
            nome_pedido =dados['nome_pedido'],
            valor_pedido =dados['valor_pedido'],
            quantidade_pedido =dados['quantidade_pedido']
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



