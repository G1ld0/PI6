<template>
  <div class="detail-container">
    <div v-if="loading" class="loading-message">
      <p>Verificando cápsula...</p>
    </div>

    <div v-if="error" class="error-message">
      <h2>Erro</h2>
      <p>{{ error }}</p>
      <router-link to="/capsules">Voltar</router-link>
    </div>

    <div v-if="!loading && !error">
      <div v-if="checkResult && !checkResult.can_open" class="capsule-locked">
        <h2>🔒 Cápsula Trancada</h2>
        <p>{{ checkResult.reason }}</p>
        
        <p v-if="capsuleDate">Data de liberação: {{ formatDate(capsuleDate) }}</p>
        
        <div v-if="capsuleLatLgn" class="location-map-container">
          <LocationMap :lat="capsuleLatLgn.lat" :lng="capsuleLatLgn.lng" />
        </div>
        
        <button @click="reCheck" class="recheck-btn">Tentar novamente</button>
      </div>

      <div v-if="checkResult && checkResult.can_open && capsule">
        
        <div v-if="capsule.tipo === 'fisica'" class="capsule-open capsule-physical">
          <h2>🤖 Cápsula Física Destrancada</h2>
          <p>Um sinal foi enviado para o seu dispositivo IoT.</p>
          <p>A cápsula '<strong>{{ capsule.message }}</strong>' foi liberada.</p>
        </div>
        
        <div v-else class="capsule-open">
          <h2>Cápsula Aberta!</h2>
          
          <p v-if="capsule.message" class="message-text">
            {{ capsule.message }}
          </p>
          
          <div v-if="capsule.media_files && capsule.media_files.length > 0" class="media-gallery">
            <h3>Suas Mídias:</h3>
            <div 
              v-for="media in capsule.media_files" 
              :key="media.url" 
              class="media-item"
            >
              <img v-if="media.type === 'image'" :src="media.url" alt="Mídia da cápsula">
              <video v-else-if="media.type === 'video'" :src="media.url" controls></video>
              <audio v-else-if="media.type === 'audio'" :src="media.url" controls></audio>
            </div>
          </div>
        </div>

        <router-link to="/capsules" class="back-link">Voltar</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import LocationMap from '../components/LocationMap.vue'
// [CORREÇÃO DE FUSO] Importa 'date-fns'
import { format, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'

const route = useRoute()
const authStore = useAuthStore()

const capsule = ref(null)
const loading = ref(true)
const error = ref(null)
const checkResult = ref(null)
const capsuleDate = ref(null)
const capsuleLatLgn = ref(null) 

const capsuleId = route.params.id

const getCurrentLocation = () => {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      console.warn('Geolocalização não suportada.')
      resolve({ lat: null, lng: null })
      return
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lng: position.coords.longitude
        })
      },
      (err) => {
        console.warn('Usuário negou geolocalização.', err.message)
        resolve({ lat: null, lng: null })
      }
    )
  })
}

const fetchCapsule = async () => {
  loading.value = true
  error.value = null
  
  if (!authStore.token) {
    error.value = "Você não está autenticado."
    loading.value = false
    return
  }

  try {
    const location = await getCurrentLocation()

    const checkResponse = await axios.get(
      `${import.meta.env.VITE_API_URL}/capsules/${capsuleId}/check`,
      {
        params: {
          lat: location.lat,
          lng: location.lng
        },
        headers: { Authorization: `Bearer ${authStore.token}` }
      }
    )
    
    checkResult.value = checkResponse.data

    // 2. Busca os dados completos da cápsula (SEMPRE)
    // para mostrar a data de liberação (se estiver trancada)
    // ou o conteúdo (se estiver aberta)
    try {
      const capsuleInfo = await axios.get(
        `${import.meta.env.VITE_API_URL}/capsules/${capsuleId}`,
        { headers: { Authorization: `Bearer ${authStore.token}` } }
      )
      
      // Se pode abrir, salva os dados completos
      if (checkResult.value.can_open) {
        capsule.value = capsuleInfo.data
      } else {
        // Se está trancada, salva apenas a data e localização para mostrar
        capsuleDate.value = capsuleInfo.data.release_date
        if (capsuleInfo.data.lat && capsuleInfo.data.lng) {
          capsuleLatLgn.value = { lat: capsuleInfo.data.lat, lng: capsuleInfo.data.lng }
        }
      }

    } catch (infoError) {
      // Falha ao buscar os dados da cápsula (ex: Erro 500)
      error.value = infoError.response?.data?.error || 'Erro ao carregar dados da cápsula.'
    }

  } catch (err) {
    // Falha ao fazer o CHECK (ex: Erro 500 no /check)
    if (err.response) {
      error.value = err.response.data?.error || 'Erro ao verificar cápsula.'
    } else {
      error.value = 'Erro de rede ou servidor indisponível.'
    }
  } finally {
    loading.value = false
  }
}

// [CORREÇÃO DE FUSO]
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = parseISO(dateString) // Lê a data UTC
  return format(date, 'dd MMMM yyyy \'às\' HH:mm', { locale: ptBR }) // Formata para local
}

const reCheck = () => {
  fetchCapsule()
}

onMounted(() => {
  fetchCapsule()
})
</script>

<style scoped>
/* Os seus estilos ... */
.detail-container { max-width: 900px; margin: 2rem auto; padding: 2rem; background: #35495e; border-radius: 8px; color: white; }
.loading-message, .error-message { text-align: center; }
.error-message h2 { color: #e74c3c; }
.capsule-locked { text-align: center; padding: 2rem; background: rgba(0,0,0,0.2); border-radius: 8px; }
.capsule-locked h2 { font-size: 2rem; }
.location-map-container { width: 100%; height: 300px; margin: 1.5rem auto; border-radius: 8px; overflow: hidden; background: #a2d9ff; }
.recheck-btn { margin-top: 1rem; padding: 0.75rem 1.5rem; background: #42b983; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 1rem; }
.recheck-btn:hover { background: #3aa876; }
.capsule-open h2 { text-align: center; color: #42b983; font-size: 2.2rem; margin-bottom: 1.5rem; }
.message-text { font-size: 1.2rem; line-height: 1.6; white-space: pre-wrap; background: rgba(0,0,0,0.1); padding: 1rem; border-radius: 4px; }
.media-gallery { margin-top: 2rem; }
.media-gallery h3 { border-bottom: 2px solid #42b983; padding-bottom: 0.5rem; margin-bottom: 1rem; }
.media-item { margin-bottom: 1.5rem; }
.media-item img, .media-item video { width: 100%; max-width: 100%; border-radius: 4px; }
.media-item audio { width: 100%; }
.back-link { display: inline-block; margin-top: 2rem; color: #42b983; text-decoration: none; }

/* [MUDANÇA] Estilo para a cápsula física destrancada */
.capsule-physical {
  text-align: center;
}
.capsule-physical h2 {
  color: #f39c12; /* Cor diferente para IoT */
}
.capsule-physical p {
  font-size: 1.1rem;
  line-height: 1.6;
}
</style>