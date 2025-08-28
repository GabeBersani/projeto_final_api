import sqlalchemy
from dateutil.relativedelta import relativedelta
from flask import Flask, jsonify, redirect, request
from flask_pydantic_spec import FlaskPydanticSpec
from datetime import date, datetime, timedelta
from functools import wraps
from models import Funcionario, Aluno, Salgado, Doce, Bebida, Pedido, SessionLocalExemplo
from datetime import date
# from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from flask_jwt_extended import get_jwt_identity, JWTManager, create_access_token, jwt_required
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super_senha"
jwt = JWTManager(app)

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        print(f'c_user:{current_user}')
        db = SessionLocalExemplo()
        try:
            sql = select(Funcionario).where(Funcionario.email == current_user)
            user = db.execute(sql).scalar()
            print(f'teste admin: {user and user.papel == "admin"} {user.papel}')
            if user and user.papel == "admin":
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

    db = SessionLocalExemplo()

    try:
        sql = select(Funcionario).where(Funcionario.email == email)
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




