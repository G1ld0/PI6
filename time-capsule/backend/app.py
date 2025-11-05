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
from datetime import datetime, timezone # Importa timezone
import traceback 
import paho.mqtt.client as mqtt
import ssl
import json
from flask_apscheduler import APScheduler

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

# --- CÓDIGO MQTT E AGENDADOR ---

# Credenciais do HiveMQ
MQTT_BROKER_URL = "06bcdf1d27ac416eaeee25f7ba3f6331.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "Univesp_pji6"
MQTT_PASSWORD = "Admin_pji6"
MQTT_TOPIC = "capsulatempo/expira/cps-001"

# Configuração do Agendador
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# No seu backend/app.py

# No seu backend/app.py

def publish_to_mqtt(payload_json):
    """
    Conecta-se ao broker HiveMQ via TLS e publica uma mensagem.
    [VERSÃO MAIS ATUAL - v2.x]
    """
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        
        # [MUDANÇA] Sintaxe nova v2.x para TLS, com o 'transport'
        # Isto agora irá funcionar porque o requirements.txt força a v2.x
        client.tls_set(transport="tcp", tls_version=ssl.PROTOCOL_TLSv1_2)
        client.tls_insecure_set(False) # Garante que o certificado seja validado
        
        print(f"Tentando conectar ao broker MQTT (v2): {MQTT_BROKER_URL}...")
        client.connect(MQTT_BROKER_URL, MQTT_PORT, 60)
        
        client.publish(MQTT_TOPIC, json.dumps(payload_json))
        
        client.loop_start()
        client.disconnect()
        client.loop_stop()
        print(f"Mensagem publicada com sucesso no tópico: {MQTT_TOPIC}")
        return True

    except Exception as e:
        print(f"!!!!!! ERRO AO PUBLICAR NO MQTT (v2) !!!!!!")
        traceback.print_exc()
        return False

def check_expired_capsules():
    """
    Função que o scheduler irá executar a cada minuto, usando a hora local (GMT-3).
    """
    # Esta função agora usa o contexto da app flask,
    # que por sua vez usa o TZ='America/Sao_Paulo' definido no Render.
    with app.app_context():
        print(f"[{datetime.now()}] Executando job: Verificando cápsulas físicas expiradas...")
        try:
            # [MUDANÇA DE LÓGICA]
            # O servidor está em GMT-3, então pegamos a hora local
            now_local_iso = datetime.now().isoformat()
            
            # Busca cápsulas FÍSICAS, VENCIDAS (na hora local) e NÃO NOTIFICADAS
            response = supabase.table('capsules') \
                .select('id, release_date, message') \
                .eq('tipo', 'fisica') \
                .eq('notificacao_enviada', False) \
                .lte('release_date', now_local_iso) \
                .execute()

            if not response.data:
                print("Nenhuma cápsula física nova para notificar.")
                return

            print(f"Encontradas {len(response.data)} cápsulas físicas para processar.")

            for capsule in response.data:
                print(f"Processando cápsula ID: {capsule['id']}...")
                
                payload = {
                    "capsula": {
                        "id": str(capsule['id']),
                        "tipo": "fisica",
                        "tempo": { "abrir_em": capsule['release_date'] },
                        "conteudo": { "mensagem": capsule.get('message', 'Cápsula física pronta!') }
                    }
                }
                
                if publish_to_mqtt(payload):
                    supabase.table('capsules') \
                        .update({'notificacao_enviada': True}) \
                        .eq('id', capsule['id']) \
                        .execute()
                    print(f"Cápsula {capsule['id']} marcada como notificada.")
                else:
                    print(f"Falha ao publicar MQTT para a cápsula {capsule['id']}. Tentará novamente no próximo minuto.")

        except Exception as e:
            print("!!!!!! ERRO NO JOB AGENDADO 'check_expired_capsules' !!!!!!")
            traceback.print_exc()

@scheduler.task('interval', id='job_check_capsules', seconds=60, misfire_grace_time=900)
def scheduled_job():
    check_expired_capsules()

# --- FIM CÓDIGO MQTT E AGENDADOR ---


# --- ROTAS DA APLICAÇÃO ---

@app.route('/test-mqtt')
def test_mqtt():
    """ Rota de teste para forçar uma publicação MQTT. """
    print("Forçando publicação MQTT de teste...")
    payload_teste = {
        "capsula": {
            "id": "teste-12345",
            "tipo": "fisica",
            "tempo": {"abrir_em": datetime.now().isoformat()},
            "conteudo": {"mensagem": "Teste manual da rota!"}
        }
    }
    if publish_to_mqtt(payload_teste):
        return "Mensagem MQTT de teste enviada com sucesso!"
    else:
        return "Falha ao enviar mensagem MQTT de teste. Verifique os logs.", 500

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
        return jsonify({ "access_token": access_token, "user_id": auth_data.user.id }), 200
    except Exception as e:
        print(f"Erro no login: {str(e)}")
        traceback.print_exc() 
        return jsonify({"error": str(e)}), 401

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
            "release_date": data['open_date'], # Salva a hora local (naive)
            "lat": data.get('lat'),
            "lng": data.get('lng'),
            "user_id": current_user_id,
            "tipo": data.get('tipo', 'digital')
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
        return jsonify({ "status": "success", "capsule_id": capsule_id }), 201
    except Exception as e:
        print(f"\nErro na criação da cápsula: {str(e)}")
        traceback.print_exc() 
        if 'capsule_id' in locals():
            supabase.table('capsules').delete().eq('id', capsule_id).execute()
        return jsonify({ "error": "Erro ao processar a requisição", "details": str(e) }), 500

@app.route('/capsules', methods=['GET'])
@jwt_required()
def list_capsules():
    try:
        user_id = get_jwt_identity()
        select_query = 'id,message,image_url,release_date,lat,lng,created_at,tipo'
        response = supabase.table('capsules').select(select_query).eq('user_id', user_id).execute()
        return jsonify({"capsules": response.data}), 200
    except Exception as e:
        print(f"Erro ao listar cápsulas: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/capsules/<capsule_id>', methods=['GET'])
@jwt_required()
def get_capsule(capsule_id):
    try:
        user_id = get_jwt_identity()
        response = supabase.table('capsules') \
                         .select('*') \
                         .eq('id', capsule_id) \
                         .eq('user_id', user_id) \
                         .execute()
        if not response.data:
            return jsonify({"error": "Cápsula não encontrada ou pertence a outro usuário"}), 404
        capsule_data = response.data[0]
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
        traceback.print_exc()
        return jsonify({"error": "Erro interno do servidor", "details": str(e)}), 500

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

        # [MUDANÇA DE LÓGICA]
        # O servidor agora está em GMT-3 (devido ao TZ=America/Sao_Paulo)
        now_local = datetime.now() 
        
        # O banco de dados agora guarda a hora local (naive)
        release_date_local = datetime.fromisoformat(capsule['release_date'])
        
        # A comparação agora é Local vs Local
        if now_local < release_date_local:
            return jsonify({
                "can_open": False,
                "reason": f"Disponível em {release_date_local.strftime('%d/%m/%Y %H:%M')}"
            }), 200

        if capsule['lat'] and capsule['lng']:
            if user_lat is None or user_lng is None:
                return jsonify({ "can_open": False, "reason": "Esta cápsula requer sua localização. Por favor, habilite-a." }), 200
            
            distance = calculate_distance( capsule['lat'], capsule['lng'], user_lat, user_lng )
            
            if distance > 0.1:  # 100 metros
                return jsonify({ "can_open": False, "reason": "Você não está no local correto" }), 200

        return jsonify({"can_open": True}), 200

    except Exception as e:
        print(f"Erro ao checar cápsula: {str(e)}")
        traceback.print_exc() 
        return jsonify({"error": str(e)}), 500

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))