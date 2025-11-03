<template>
  <div class="create-container">
    <h1>Criar nova cápsula do tempo</h1>
    
    <form @submit.prevent="handleSubmit" class="capsule-form">
      <div class="form-group">
        <label for="message">Mensagem (Opcional)</label>
        <textarea 
          id="message" 
          v-model="message" 
          placeholder="Escreva sua mensagem para o futuro..."
          rows="5"
        ></textarea>
      </div>
      
      <div class="form-group">
        <label for="files">Arquivos (Opcional)</label>
        <input 
          type="file" 
          id="files" 
          accept="image/*,video/*,audio/*" 
          multiple
          @change="handleFileSelection"
        >
        <div v-if="selectedFiles.length > 0" class="file-preview-list">
          <p>{{ selectedFiles.length }} arquivo(s) selecionado(s):</p>
          <ul>
            <li v-for="file in selectedFiles" :key="file.name">
              {{ file.name }} ({{ getFileType(file.type) }})
            </li>
          </ul>
        </div>
      </div>
      
      <div class="form-group">
        <label for="release_date">Data de Liberação</label>
        <input 
          type="datetime-local" 
          id="release_date" 
          v-model="release_date" 
          required
        >
      </div>
      
      <div class="form-group">
        <label>
          <input type="checkbox" v-model="useLocation"> 
          Liberar apenas em um local específico
        </label>
        
        <div v-if="useLocation" class="location-fields">
          <div class="form-group">
            <label for="lat">Latitude</label>
            <input
              type="text"
              id="lat"
              :value="lat !== null ? lat.toFixed(10) : ''"
              @input="lat = $event.target.value ? Number($event.target.value) : null"
              placeholder="Ex: -23.5505000000"
            />
          </div>
          <div class="form-group">
            <label for="lng">Longitude</label>
            <input
              type="text"
              id="lng"
              :value="lng !== null ? lng.toFixed(10) : ''"
              @input="lng = $event.target.value ? Number($event.target.value) : null"
              placeholder="Ex: -46.6333000000"
            />
          </div>
          <div id="map" class="location-map"></div>
          <button 
            type="button" 
            @click="getCurrentLocation"
            class="location-btn"
          >
            Usar minha localização atual
          </button>
        </div>
      </div>
      
      <button type="submit" :disabled="isSubmitting" class="submit-btn">
        {{ isSubmitting ? 'Criando...' : 'Criar Cápsula' }}
      </button>
      
      <p v-if="error" class="error-message">{{ error }}</p>
      <p v-if="success" class="success-message">{{ success }}</p>
    </form>
  </div>
</template>

<script setup>
import 'leaflet/dist/leaflet.css'
import { ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { supabase } from '../composables/useSupabase' // Importa o cliente Supabase
import L from 'leaflet'
import { v4 as uuidv4 } from 'uuid' // Para gerar nomes de arquivo únicos

const message = ref('')
const selectedFiles = ref([]) // Armazena os ARQUIVOS (File objects)
const release_date = ref('')
const useLocation = ref(false)
const lat = ref(null)
const lng = ref(null)
const isSubmitting = ref(false)
const error = ref(null)
const success = ref(null)
const router = useRouter()
const authStore = useAuthStore()

let map, marker

watch(useLocation, async (val) => {
  if (val) {
    await nextTick()
    if (!map) {
      map = L.map('map').setView([lat.value || -23.5505, lng.value || -46.6333], 13)
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(map)
      marker = L.marker([lat.value || -23.5505, lng.value || -46.6333], { draggable: true }).addTo(map)
      marker.on('dragend', function(e) {
        const pos = e.target.getLatLng()
        lat.value = pos.lat
        lng.value = pos.lng
      })
    } else {
      map.invalidateSize()
    }
  } else {
    if (map) {
      map.remove()
      map = null
      marker = null
    }
  }
})

watch([lat, lng], ([newLat, newLng]) => {
  if (marker && map && newLat && newLng) {
    marker.setLatLng([newLat, newLng])
    map.setView([newLat, newLng])
  }
})

// Armazena os arquivos selecionados na ref
const handleFileSelection = (event) => {
  selectedFiles.value = Array.from(event.target.files)
}

// Converte o tipo MIME para um tipo simples (image, video, audio)
const getFileType = (mimeType) => {
  if (mimeType.startsWith('image/')) return 'image'
  if (mimeType.startsWith('video/')) return 'video'
  if (mimeType.startsWith('audio/')) return 'audio'
  return 'other'
}

const getCurrentLocation = () => {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        lat.value = position.coords.latitude
        lng.value = position.coords.longitude
      },
      (err) => {
        error.value = 'Erro ao obter localização: ' + err.message
      }
    )
  } else {
    error.value = 'Geolocalização não suportada pelo navegador'
  }
}

// [MUDANÇA AQUI] Lógica de envio totalmente nova
const handleSubmit = async () => {
  // Validação: Pelo menos uma mensagem ou um arquivo
  if (!message.value && selectedFiles.value.length === 0) {
    error.value = 'Você deve adicionar uma mensagem ou pelo menos um arquivo.'
    return
  }

  isSubmitting.value = true
  error.value = null
  success.value = null

  try {
    const media_files = [] // Array para guardar os links do storage
    const userId = authStore.userId // Pega o ID do usuário da sua store

    if (!userId) {
      throw new Error("Usuário não autenticado. Faça login novamente.")
    }

    // 1. Fazer o upload de cada arquivo para o Supabase Storage
    for (const file of selectedFiles.value) {
      const fileType = getFileType(file.type)
      if (fileType === 'other') continue // Pula arquivos desconhecidos

      const fileExt = file.name.split('.').pop()
      // Cria um caminho único no Storage
      const filePath = `user_${userId}/${uuidv4()}.${fileExt}`

      // Faz o upload para o bucket 'capsule-media'
      // ATENÇÃO: O bucket do seu app.py era 'capsule-media'.
      // Se for outro, mude o nome aqui.
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from('capsule-media') // Nome do seu bucket
        .upload(filePath, file, {
          contentType: file.type
        })

      if (uploadError) {
        throw new Error(`Erro no upload do arquivo ${file.name}: ${uploadError.message}`)
      }
      
      // Adiciona o arquivo à lista que será enviada ao backend
      media_files.push({
        storage_path: uploadData.path, // O caminho salvo
        media_type: fileType
      })
    }

    // 2. Montar o payload final para o backend Flask
    const payload = {
      message: message.value || null, // Envia null se estiver vazio
      media_files: media_files,
      open_date: release_date.value,
      lat: useLocation.value ? lat.value : null,
      lng: useLocation.value ? lng.value : null
    }

    // 3. Enviar o payload para o backend Flask
    await axios.post(`${import.meta.env.VITE_API_URL}/capsules`, payload, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    })

    success.value = 'Cápsula criada com sucesso!'
    setTimeout(() => {
      router.push('/capsules')
    }, 1500)

  } catch (err) {
    // Tratamento de erro
    if (err.response) {
      error.value = err.response.data?.error || 'Erro do servidor'
    } else if (err.request) {
      error.value = 'Sem resposta do servidor. Verifique sua conexão.'
    } else {
      error.value = err.message || 'Erro ao criar cápsula'
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.create-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.capsule-form {
  background: #35495e;/*#fff;*/
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

input[type="text"],
input[type="number"],
input[type="datetime-local"],
input[type="file"],
textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

textarea {
  resize: vertical;
}

/* Novo: Estilo para a lista de arquivos */
.file-preview-list {
  margin-top: 1rem;
  background: #4a6580;
  padding: 0.5rem 1rem;
  border-radius: 4px;
}
.file-preview-list ul {
  list-style-type: disc;
  margin-left: 20px;
}

.location-fields {
  color: #2c3e50;
  margin-top: 1rem;
  padding: 1rem;
  background: #f5f5f5;
  border-radius: 4px;
}

.location-fields input[type="number"] {
  color: #2c3e50;
  background: #fff;
  border: 1.5px solid #35495e;
  font-weight: bold;
}

.location-map {
  width: 100%;
  height: 300px;
  margin-top: 1rem;
  border-radius: 8px;
  z-index: 1;
}

.location-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 0.5rem;
}

.location-btn:hover {
  background: #2980b9;
}

.submit-btn {
  background: #42b983;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  width: 100%;
}

.submit-btn:hover {
  background: #3aa876;
}

.submit-btn:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

.error-message {
  color: #e74c3c;
  margin-top: 1rem;
}

.success-message {
  color: #2ecc71;
  margin-top: 1rem;
}
</style>