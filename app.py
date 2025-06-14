from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(100), nullable=False)
    photo_url = db.Column(db.String(300))

class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receiver = db.Column(db.String(100), nullable=False)
    cep = db.Column(db.String(20), nullable=False)
    street = db.Column(db.String(200), nullable=False)
    number = db.Column(db.String(20), nullable=False)
    complement = db.Column(db.String(100))
    neighborhood = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), nullable=False, default='Pendente')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    received_by = db.Column(db.String(100))
    cpf_receiver = db.Column(db.String(20))
    relation = db.Column(db.String(50))
    photo_url = db.Column(db.String(200))

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not all(k in data for k in ("name", "email", "phone", "password")):
        return jsonify({'message': 'Todos os campos são obrigatórios!'}), 400

    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'message': 'E-mail já cadastrado!'}), 400

    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    user = User(
        name=data['name'],
        email=data['email'],
        phone=data['phone'],
        password=hashed_password,
        photo_url=data.get('photo_url')
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'Usuário cadastrado com sucesso!'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()

    if user and check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Login bem-sucedido!', 'user_id': user.id}), 200
    else:
        return jsonify({'message': 'Credenciais inválidas'}), 400

@app.route('/users/<int:id>', methods=['GET', 'PUT'])
def user_details(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'Usuário não encontrado'}), 404

    if request.method == 'GET':
        return jsonify({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'photo_url': user.photo_url
        }), 200

    if request.method == 'PUT':
        data = request.get_json()
        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        user.phone = data.get('phone', user.phone)
        user.photo_url = data.get('photo_url', user.photo_url)
        db.session.commit()
        return jsonify({'message': 'Usuário atualizado com sucesso!'}), 200

@app.route('/deliveries', methods=['POST'])
def add_delivery():
    data = request.get_json()

    required_fields = ["receiver", "cep", "street", "number", "neighborhood", "city", "state", "description", "user_id", "status"]
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Todos os campos obrigatórios devem ser preenchidos.'}), 400

    delivery = Delivery(
        receiver=data['receiver'],
        cep=data['cep'],
        street=data['street'],
        number=data['number'],
        complement=data.get('complement', ''),
        neighborhood=data['neighborhood'],
        city=data['city'],
        state=data['state'],
        description=data['description'],
        status=data['status'],
        user_id=data['user_id']
    )

    db.session.add(delivery)
    db.session.commit()
    return jsonify({'message': 'Entrega cadastrada com sucesso!'}), 201

@app.route('/deliveries/user/<int:user_id>', methods=['GET'])
def get_deliveries_by_user(user_id):
    deliveries = Delivery.query.filter_by(user_id=user_id).all()
    result = []
    for d in deliveries:
        result.append({
            'id': d.id,
            'receiver': d.receiver,
            'cep': d.cep,
            'street': d.street,
            'number': d.number,
            'complement': d.complement,
            'neighborhood': d.neighborhood,
            'city': d.city,
            'state': d.state,
            'description': d.description,
            'status': d.status,
            'received_by': d.received_by,
            'cpf_receiver': d.cpf_receiver,
            'relation': d.relation,
            'photo_url': d.photo_url
        })
    return jsonify(result), 200

@app.route('/deliveries/<int:id>', methods=['GET'])
def get_delivery(id):
    delivery = Delivery.query.get(id)
    if not delivery:
        return jsonify({'message': 'Entrega não encontrada'}), 404

    return jsonify({
        'id': delivery.id,
        'receiver': delivery.receiver,
        'cep': delivery.cep,
        'street': delivery.street,
        'number': delivery.number,
        'complement': delivery.complement,
        'neighborhood': delivery.neighborhood,
        'city': delivery.city,
        'state': delivery.state,
        'description': delivery.description,
        'status': delivery.status,
        'received_by': delivery.received_by,
        'cpf_receiver': delivery.cpf_receiver,
        'relation': delivery.relation,
        'photo_url': delivery.photo_url
    }), 200

@app.route('/deliveries/<int:id>/confirm', methods=['PUT'])
def confirm_delivery(id):
    delivery = Delivery.query.get(id)
    if not delivery:
        return jsonify({'message': 'Entrega não encontrada'}), 404

    data = request.get_json()
    delivery.received_by = data['received_by']
    delivery.cpf_receiver = data['cpf_receiver']
    delivery.relation = data['relation']
    delivery.photo_url = data['photo_url']
    delivery.status = 'Concluído'

    db.session.commit()
    return jsonify({'message': 'Entrega confirmada com sucesso!'}), 200

@app.route('/deliveries/details/<int:id>', methods=['GET'])
def get_delivery_details(id):
    delivery = Delivery.query.get(id)
    if not delivery:
        return jsonify({'message': 'Entrega não encontrada'}), 404

    user = User.query.get(delivery.user_id)
    if not user:
        return jsonify({'message': 'Usuário não encontrado'}), 404

    return jsonify({
        'id': delivery.id,
        'receiver': delivery.receiver,
        'cep': delivery.cep,
        'street': delivery.street,
        'number': delivery.number,
        'complement': delivery.complement,
        'neighborhood': delivery.neighborhood,
        'city': delivery.city,
        'state': delivery.state,
        'description': delivery.description,
        'status': delivery.status,
        'received_by': delivery.received_by,
        'cpf_receiver': delivery.cpf_receiver,
        'relation': delivery.relation,
        'photo_url': delivery.photo_url,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email
        }
    }), 200

def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=5000, debug=True)
