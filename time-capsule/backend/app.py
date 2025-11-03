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
            "https://time-capsule20.vercel.app",
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
@app.route('/login', methods=['POST'])
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
# No arquivo backend/app.py

@app.route('/capsules', methods=['POST'])
@jwt_required()  # Exige autenticação via JWT
def create_capsule():
    """
    Cria uma cápsula no Supabase com mensagem, data, localização
    e uma lista de mídias (fotos, vídeos, áudios) já enviadas
    para o Supabase Storage pelo frontend.

    Corpo da requisição (JSON) esperado:
    {
        "message": "Texto da cápsula (opcional)",
        "media_files": [
            { "storage_path": "caminho/no/storage/imagem.png", "media_type": "image" },
            { "storage_path": "caminho/no/storage/video.mp4", "media_type": "video" },
            { "storage_path": "caminho/no/storage/audio.mp3", "media_type": "audio" }
        ],
        "open_date": "2025-12-31T23:59:59",
        "lat": -23.5505 (opcional, pode ser null),
        "lng": -46.6333 (opcional, pode ser null)
    }
    """
    try:
        # Força a leitura como JSON mesmo sem header
        data = request.get_json(force=True, silent=True)
        
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        current_user_id = get_jwt_identity() # Obtém o ID do usuário do token (user_id)

        # 1. Validação dos campos
        # A data de abertura é obrigatória
        if 'open_date' not in data:
            return jsonify({"error": "Campo 'open_date' é obrigatório"}), 400
        
        # Pelo menos uma mensagem ou um arquivo de mídia deve existir
        message = data.get('message')
        media_files = data.get('media_files', [])
        
        if not message or not media_files:
            return jsonify({"error": "A cápsula deve conter ao menos uma mensagem ou um arquivo de mídia"}), 400

        # 2. Criação da Cápsula principal no banco
        response_capsule = supabase.table('capsules').insert({
            "message": message,
            "release_date": data['open_date'],
            "lat": data.get('lat'), # .get() aceita valores nulos
            "lng": data.get('lng'),
            "user_id": current_user_id
        }).execute()

        if not response_capsule.data:
            raise Exception("Falha ao inserir na tabela 'capsules'")

        capsule_id = response_capsule.data[0]['id']

        # 3. Insere os arquivos de mídia na nova tabela 'capsule_media'
        if media_files:
            media_to_insert = []
            for media in media_files:
                if 'storage_path' in media and 'media_type' in media:
                    media_to_insert.append({
                        "capsule_id": capsule_id,
                        "storage_path": media['storage_path'],
                        "media_type": media['media_type']
                    })
            
            if media_to_insert:
                response_media = supabase.table('capsule_media').insert(media_to_insert).execute()
                if not response_media.data:
                    # Se falhar aqui, idealmente deveríamos deletar a cápsula (rollback)
                    # Mas por simplicidade, vamos apenas reportar o erro
                    raise Exception("Falha ao inserir mídias na tabela 'capsule_media'")

        return jsonify({
            "status": "success",
            "capsule_id": capsule_id
        }), 201

    except Exception as e:
        print("\nErro na criação da cápsula:", str(e))
        # Tenta deletar a cápsula principal se a inserção de mídias falhar
        if 'capsule_id' in locals():
            supabase.table('capsules').delete().eq('id', capsule_id).execute()
        
        return jsonify({
            "error": "Erro ao processar a requisição",
            "details": str(e)
        }), 500


@app.route('/capsules', methods=['GET'])
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


@app.route('/capsules/<capsule_id>', methods=['GET'])
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

@app.route('/capsules/<capsule_id>/check', methods=['GET'])
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