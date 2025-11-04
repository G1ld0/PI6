@app.route('/capsules/<capsule_id>', methods=['GET'])
@jwt_required()
def get_capsule(capsule_id):
    """
    Busca uma cápsula específica e todos os seus arquivos de mídia.
    """
    try:
        user_id = get_jwt_identity()
        
        # 1. Busca a cápsula principal
        # Usamos .single() para garantir que retorne um objeto, ou um erro se não achar
        response = supabase.table('capsules') \
                         .select('*') \
                         .eq('id', capsule_id) \
                         .eq('user_id', user_id) \
                         .single() \
                         .execute()
        
        # response.data já será o objeto da cápsula, não uma lista
        capsule_data = response.data
        
        # 2. Busca as mídias associadas
        response_media = supabase.table('capsule_media') \
                               .select('media_type, storage_path') \
                               .eq('capsule_id', capsule_id) \
                               .execute()
        
        media_files_with_urls = []
        
        if response_media.data:
            for media in response_media.data:
                # 3. GERA A URL PÚBLICA PARA O FRONTEND
                # Lembre-se que seu bucket se chama 'capsule-media'
                public_url = supabase.storage.from_('capsule-media') \
                                           .get_public_url(media['storage_path'])
                
                media_files_with_urls.append({
                    "type": media['media_type'],
                    "url": public_url
                })
        
        # 4. Combina tudo no objeto da cápsula
        capsule_data['media_files'] = media_files_with_urls
        
        return jsonify(capsule_data), 200
        
    except Exception as e:
        print(f"Erro ao buscar cápsula: {str(e)}")
        # Trata o erro específico do .single() se não encontrar a cápsula
        if 'PGRST116' in str(e) or '0 rows' in str(e):
             return jsonify({"error": "Cápsula não encontrada ou pertence a outro usuário"}), 404
        return jsonify({"error": "Erro interno do servidor", "details": str(e)}), 500