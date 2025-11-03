# Importações necessárias
from flask import Flask, request, jsonify
from supabase import create_client
import os
from dotenv import load_dotenv
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    get_jwt_identity,
    create_access_token
)
import uuid
from math import radians, sin, cos, sqrt, atan2
from flask_cors import CORS

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializa a aplicação Flask
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://time-capsule20.vercel.app/",
            "http://localhost:5173"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

# Configuração do JWT (JSON Web Tokens)
# A chave secreta é usada para assinar os tokens
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
jwt = JWTManager(app)

# Inicializa o cliente Supabase
# As credenciais são lidas do arquivo .env
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Rota de teste para verificar se o backend está funcionando
@app.route('/')
def hello():
    return "Backend do Time Capsule funcionando"

# Rota de login
@app.route('/api/login', methods=['POST'])
def login():
    """
    Autentica usuário via Supabase Auth e retorna um JWT.
    Corpo da requisição (JSON):
    {
        "email": "user@example.com",
        "password": "senha123"
    }
    Retorno:
    {
        "access_token": "token_jwt_aqui"
    }
    """
    try:
        data = request.get_json(force=True)  # Força a leitura como JSON
        
        # Validação básica dos campos
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Email e senha são obrigatórios"}), 400


        # Autenticação no Supabase
        auth_data = supabase.auth.sign_in_with_password({
            "email": data['email'],
            "password": data['password']
        })
        
        # Cria um token JWT com o ID do usuário
        access_token = create_access_token(identity=auth_data.user.id)
        return jsonify({
            "access_token": access_token,
            "user_id": auth_data.user.id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 401

# Rota para criar cápsulas
@app.route('/api/capsules', methods=['POST'])
@jwt_required()  # Exige autenticação via JWT
def create_capsule():
    """
    Cria uma cápsula no Supabase com mensagem, imagem, data e localização.
    Corpo da requisição (JSON):
    {
        "message": "Texto da cápsula",
        "image_base64": "data:image/jpeg;base64,...",
        "open_date": "2025-12-31T23:59:59",
        "lat": -23.5505,
        "lng": -46.6333
    }
    """
    try:
        # Força a leitura como JSON mesmo sem header
        data = request.get_json(force=True, silent=True)
        
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        current_user_id = get_jwt_identity()  # Obtém o ID do usuário do token (user_id)

        # Campos obrigatórios
        required_fields = ["message", "image_base64", "open_date", "lat", "lng"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": f"Campos obrigatórios faltando: {required_fields}"}), 400

        # Processamento da imagem
        try:
            # Separa o header do base64 (se existir)
            if ',' in data['image_base64']:
                header, image_data = data['image_base64'].split(',', 1)
            else:
                image_data = data['image_base64']
            
            # Decodifica o base64 para bytes
            import base64
            image_bytes = base64.b64decode(image_data)
            
            # Determina a extensão do arquivo
            file_extension = 'jpg'  # padrão
            if 'image/png' in header:
                file_extension = 'png'
            elif 'image/gif' in header:
                file_extension = 'gif'
            
            # Gera um nome único para o arquivo
            import uuid
            file_name = f"user_{current_user_id}/{uuid.uuid4()}.{file_extension}"
            
        except Exception as e:
            return jsonify({"error": "Imagem em formato inválido", "details": str(e)}), 400

        # Faz upload para o Supabase Storage (nova forma de verificar erros)
        try:
            upload_response = supabase.storage.from_('capsule-images').upload(
                file_name,
                image_bytes,
                {"content-type": f"image/{file_extension}"}
            )
            
            # Verifica se houve erro no upload (nova forma)
            if isinstance(upload_response, dict) and 'error' in upload_response:
                raise Exception(upload_response['error'])
            
        except Exception as upload_error:
            raise Exception(f"Erro no upload da imagem: {str(upload_error)}")

        # Obtém URL pública da imagem
        image_url = supabase.storage.from_('capsule-images').get_public_url(file_name)

        # Criação da Cápsula no banco de dados
        response = supabase.table('capsules').insert({
            "message": data['message'],
            "image_url": image_url,
            "release_date": data['open_date'],
            "lat": data['lat'],
            "lng": data['lng'],
            "user_id": current_user_id
        }).execute()

        if not response.data:
            raise Exception("Falha ao inserir no banco de dados")

        return jsonify({
            "status": "success",
            "image_url": image_url,
            "capsule_id": response.data[0]['id']
        }), 201

    except Exception as e:
        print("\nErro na criação da cápsula:", str(e))
        return jsonify({
            "error": "Erro ao processar a requisição",
            "details": str(e)
        }), 500


@app.route('/api/capsules', methods=['GET'])
@jwt_required()
def list_capsules():
    """
    Lista todas as cápsulas do usuário autenticado.
    Retorno:
    {
        "capsules": [
            {
                "id": "uuid",
                "message": "Texto",
                "image_url": "url",
                "release_date": "datetime",
                "lat": latitude,
                "lng": longitude,
                "user_id": "uuid",
                "created_at": "datetime"
            }
        ]
    }
    """
    try:
        user_id = get_jwt_identity()
        response = supabase.table('capsules').select('id,message,image_url,release_date,lat,lng,created_at').eq('user_id', get_jwt_identity()).execute()
        
        capsules = []
        for capsule in response.data:
            formatted_capsule = {
                "id": capsule['id'],
                "message": capsule['message'],
                "image_url": capsule['image_url'],
                "release_date": capsule['release_date'],
                "lat": capsule['lat'],
                "lng": capsule['lng'],
                "created_at": capsule['created_at']
            }
            capsules.append(formatted_capsule)
        
        return jsonify({"capsules": capsules}), 200
        
    except Exception as e:
        print(f"Erro ao listar cápsulas: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/capsules/<capsule_id>', methods=['GET'])
@jwt_required()
def get_capsule(capsule_id):
    try:
        user_id = get_jwt_identity()
        
        response = supabase.table('capsules')\
                         .select('*')\
                         .eq('id', capsule_id)\
                         .eq('user_id', user_id)\
                         .execute()
        
        if not response.data:
            return jsonify({"error": "Cápsula não encontrada"}), 404
            
        return jsonify(response.data[0]), 200
        
    except Exception as e:
        print(f"Erro ao buscar cápsula: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/capsules/<capsule_id>/check', methods=['GET'])
@jwt_required()
def check_capsule(capsule_id):
    """
    Verifica se a cápsula pode ser aberta (data e localização).
    Query Params:
    - lat: Latitude atual do usuário
    - lng: Longitude atual do usuário
    Retorno:
    {
        "can_open": true/false,
        "reason": "Motivo (se não puder abrir)"
    }
    """
    try:
        # Obtem a localização do usuário através de uma argumento
        user_id = get_jwt_identity()
        user_lat = request.args.get('lat', type=float)
        user_lng = request.args.get('lng', type=float)

        # Busca a cápsula
        response = supabase.table('capsules').select('release_date,lat,lng').eq('id', capsule_id).eq('user_id', user_id).execute()
        if not response.data:
            return jsonify({"error": "Cápsula não encontrada"}), 404
        capsule = response.data[0]

        # Verifica a data
        from datetime import datetime
        now = datetime.now()
        release_date = datetime.fromisoformat(capsule['release_date'])
        if now < release_date:
            return jsonify({
                "can_open": False,
                "reason": f"Disponível em {release_date.strftime('%d/%m/%Y %H:%M')}"
            }), 200

        # Verifica localização (se existir)
        if capsule['lat'] and capsule['lng']:
            # Cálculo simples de distância em km (fórmula de Haversine)
            distance = calculate_distance(
                capsule['lat'], capsule['lng'],
                user_lat, user_lng
            )
            
            if distance > 0.1:  # 0.1 km = 100 metros
                return jsonify({
                    "can_open": False,
                    "reason": "Você não está no local correto"
                }), 200

        return jsonify({"can_open": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calcula a distância em km entre dois pontos geográficos
    usando a fórmula de Haversine
    """
    # Raio da Terra em km
    R = 6371.0

    # Converte coordenadas para radianos
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Diferenças
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Fórmula de Haversine
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

# Inicia o servidor Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000) #para uso no render