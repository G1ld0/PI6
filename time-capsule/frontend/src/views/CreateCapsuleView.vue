<template>
  <div class="create-container">
    <h1>Criar nova cápsula do tempo</h1>
    
    <form @submit.prevent="handleSubmit" class="capsule-form">
      
      <div class="form-group">
        <label for="capsuleType">Tipo de Cápsula</label>
        <select id="capsuleType" v-model="capsuleType" class="select-input" required>
          <option value="digital">Digital</option>
          <option value="fisica">Física</option>
        </select>
      </div>
      
      <div class="form-group">
        <label for="message">Mensagem (Nome da Cápsula)</label>
        <textarea 
          id="message" 
          v-model="message" 
          placeholder="Escreva sua mensagem ou nome..."
          rows="5"
          required
        ></textarea>
      </div>
      
      <div v-if="capsuleType === 'digital'" class="form-group">
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
      
      <div v-if="capsuleType === 'digital'" class="form-group">
        <label>
          <input type="checkbox" v-model="useLocation"> 
          Liberar apenas em um local específico
        </label>
        
        <div v-if="useLocation" class="location-fields">
          <div class="form-group">
            <label for="lat">Latitude</label>
            <input type="text" id="lat" v-model="lat" placeholder="Ex: -23.5505000000" />
          </div>
          <div class="form-group">
            <label for="lng">Longitude</label>
            <input type="text" id="lng" v-model="lng" placeholder="Ex: -46.6333000000" />
          </div>
          <div id="map" class="location-map"></div>
          <button type="button" @click="getCurrentLocation" class="location-btn">
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
import { supabase } from '../composables/useSupabase'
import L from 'leaflet'
import { v4 as uuidv4 } from 'uuid'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
})

const message = ref('')
const selectedFiles = ref([])
const release_date = ref('')
const capsuleType = ref('digital')
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

const handleFileSelection = (event) => {
  selectedFiles.value = Array.from(event.target.files)
}

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

const handleSubmit = async () => {
  if (!message.value) {
    error.value = 'Por favor, adicione uma mensagem (nome) para a cápsula.'
    return
  }

  isSubmitting.value = true
  error.value = null
  success.value = null

  try {
    const media_files = []
    const userId = authStore.userId

    if (!userId) {
      throw new Error("Usuário não autenticado.")
    }

    if (capsuleType.value === 'digital') {
      for (const file of selectedFiles.value) {
        const fileType = getFileType(file.type)
        if (fileType === 'other') continue
        const fileExt = file.name.split('.').pop()
        const filePath = `user_${userId}/${uuidv4()}.${fileExt}`
        const { data: uploadData, error: uploadError } = await supabase.storage
          .from('capsule-media')
          .upload(filePath, file, { contentType: file.type })
        if (uploadError) {
          throw new Error(`Erro no upload do arquivo ${file.name}: ${uploadError.message}`)
        }
        media_files.push({
          storage_path: uploadData.path,
          media_type: fileType
        })
      }
    }

    // [MUDANÇA DE LÓGICA]
    // Não convertemos mais para UTC. Enviamos a string local (naive).
    const payload = {
      message: message.value || null,
      media_files: media_files,
      open_date: release_date.value, // <-- ENVIA HORA LOCAL (ex: "2025-11-05T12:33")
      lat: (useLocation.value && capsuleType.value === 'digital') ? lat.value : null,
      lng: (useLocation.value && capsuleType.value === 'digital') ? lng.value : null,
      tipo: capsuleType.value
    }

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
.create-container { max-width: 800px; margin: 0 auto; padding: 2rem; }
.capsule-form { background: #35495e; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); }
.form-group { margin-bottom: 1.5rem; }
label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
input[type="text"], input[type="number"], input[type="datetime-local"], input[type="file"], textarea { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; }
textarea { resize: vertical; }
.file-preview-list { margin-top: 1rem; background: #4a6580; padding: 0.5rem 1rem; border-radius: 4px; }
.file-preview-list ul { list-style-type: disc; margin-left: 20px; }
.location-fields { color: #2c3e50; margin-top: 1rem; padding: 1rem; background: #f5f5f5; border-radius: 4px; }
.location-fields input[type="number"] { color: #2c3e50; background: #fff; border: 1.5px solid #35495e; font-weight: bold; }
.location-map { width: 100%; height: 300px; margin-top: 1rem; border-radius: 8px; z-index: 1; }
.location-btn { background: #3498db; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; margin-top: 0.5rem; }
.location-btn:hover { background: #2980b9; }
.submit-btn { background: #42b983; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 4px; cursor: pointer; font-size: 1rem; width: 100%; }
.submit-btn:hover { background: #3aa876; }
.submit-btn:disabled { background: #cccccc; cursor: not-allowed; }
.error-message { color: #e74c3c; margin-top: 1rem; }
.success-message { color: #2ecc71; margin-top: 1rem; }
.select-input { width: 100%; padding: 0.75rem; border: 1px solid #4a6580; background: #35495e; color: white; border-radius: 4px; font-size: 1rem; box-sizing: border-box; }
.field-description { font-size: 0.9rem; color: #c0d0e0; margin-top: 0.5rem; margin-bottom: 0; }
</style>