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
from datetime import datetime
import traceback # Importa o traceback para logs detalhados

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

# Configuração do JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
jwt = JWTManager(app)

# Inicializa o cliente Supabase
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Rota de teste
@app.route('/')
def hello():
    return "Backend do Time Capsule funcionando"

# Rota de login
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json(force=True)
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({"error": "Email e senha são obrigatórios"}), 400

        auth_data = supabase.auth.sign_in_with_password({
            "email": data['email'],
            "password": data['password']
        })
        
        access_token = create_access_token(identity=auth_data.user.id)
        return jsonify({
            "access_token": access_token,
            "user_id": auth_data.user.id
        }), 200

    except Exception as e:
        print(f"Erro no login: {str(e)}")
        traceback.print_exc() # LOG DETALHADO
        return jsonify({"error": str(e)}), 401

# Rota para criar cápsulas
@app.route('/capsules', methods=['POST'])
@jwt_required()
def create_capsule():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "Dados inválidos"}), 400

        current_user_id = get_jwt_identity()

        if 'open_date' not in data:
            return jsonify({"error": "Campo 'open_date' é obrigatório"}), 400
        
        message = data.get('message')
        media_files = data.get('media_files', [])
        
        if not message and not media_files:
            return jsonify({"error": "A cápsula deve conter ao menos uma mensagem ou um arquivo de mídia"}), 400

        response_capsule = supabase.table('capsules').insert({
            "message": message,
            "release_date": data['open_date'],
            "lat": data.get('lat'),
            "lng": data.get('lng'),
            "user_id": current_user_id
        }).execute()

        if not response_capsule.data:
            raise Exception("Falha ao inserir na tabela 'capsules'")

        capsule_id = response_capsule.data[0]['id']

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
                    raise Exception("Falha ao inserir mídias na tabela 'capsule_media'")

        return jsonify({
            "status": "success",
            "capsule_id": capsule_id
        }), 201

    except Exception as e:
        print(f"\nErro na criação da cápsula: {str(e)}")
        traceback.print_exc() # LOG DETALHADO
        if 'capsule_id' in locals():
            supabase.table('capsules').delete().eq('id', capsule_id).execute()
        return jsonify({
            "error": "Erro ao processar a requisição",
            "details": str(e)
        }), 500

# Rota para listar cápsulas
@app.route('/capsules', methods=['GET'])
@jwt_required()
def list_capsules():
    try:
        user_id = get_jwt_identity()
        response = supabase.table('capsules').select('id,message,image_url,release_date,lat,lng,created_at').eq('user_id', user_id).execute()
        
        return jsonify({"capsules": response.data}), 200
        
    except Exception as e:
        print(f"Erro ao listar cápsulas: {str(e)}")
        traceback.print_exc() # LOG DETALHADO
        return jsonify({"error": str(e)}), 500

# Rota para buscar uma cápsula
@app.route('/capsules/<capsule_id>', methods=['GET'])
@jwt_required()
def get_capsule(capsule_id):
    try:
        user_id = get_jwt_identity()
        
        response = supabase.table('capsules') \
                         .select('*') \
                         .eq('id', capsule_id) \
                         .eq('user_id', user_id) \
                         .single() \
                         .execute()
        
        capsule_data = response.data
        
        if capsule_data is None:
            return jsonify({"error": "Cápsula não encontrada ou pertence a outro usuário"}), 404
        
        response_media = supabase.table('capsule_media') \
                               .select('media_type, storage_path') \
                               .eq('capsule_id', capsule_id) \
                               .execute()
        
        media_files_with_urls = []
        if response_media.data:
            for media in response_media.data:
                public_url = supabase.storage.from_('capsule-media') \
                                           .get_public_url(media['storage_path'])
                
                media_files_with_urls.append({
                    "type": media['media_type'],
                    "url": public_url
                })
        
        capsule_data['media_files'] = media_files_with_urls
        
        return jsonify(capsule_data), 200
        
    except Exception as e:
        print(f"Erro ao buscar cápsula: {str(e)}")
        traceback.print_exc() # LOG DETALHADO
        return jsonify({"error": "Erro interno do servidor", "details": str(e)}), 500

# Rota para checar se a cápsula pode ser aberta
@app.route('/capsules/<capsule_id>/check', methods=['GET'])
@jwt_required()
def check_capsule(capsule_id):
    try:
        user_id = get_jwt_identity()
        user_lat = request.args.get('lat', type=float)
        user_lng = request.args.get('lng', type=float)

        response = supabase.table('capsules').select('release_date,lat,lng').eq('id', capsule_id).eq('user_id', user_id).execute()
        if not response.data:
            return jsonify({"error": "Cápsula não encontrada"}), 404
        capsule = response.data[0]

        now = datetime.now()
        release_date = datetime.fromisoformat(capsule['release_date'])
        
        if now < release_date:
            return jsonify({
                "can_open": False,
                "reason": f"Disponível em {release_date.strftime('%d/%m/%Y %H:%M')}"
            }), 200

        if capsule['lat'] and capsule['lng']:
            if user_lat is None or user_lng is None:
                return jsonify({
                    "can_open": False,
                    "reason": "Esta cápsula requer sua localização. Por favor, habilite-a."
                }), 200
            
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
        print(f"Erro ao checar cápsula: {str(e)}")
        traceback.print_exc() # LOG DETALHADO
        return jsonify({"error": str(e)}), 500

# Função de cálculo de distância
def calculate_distance(lat1, lon1, lat2, lon2):
    # Função 'radians' pode falhar se receber None, mas a verificação
    # 'if user_lat is None' na rota 'check_capsule' previne isso.
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Inicia o servidor Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))