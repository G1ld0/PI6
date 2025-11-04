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
        <button @click="reCheck" class="recheck-btn">Tentar novamente</button>
      </div>

      <div v-if="checkResult && checkResult.can_open && capsule" class="capsule-open">
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

        <p v-if="!capsule.message && (!capsule.media_files || capsule.media_files.length === 0)">
          Cápsula vazia.
        </p>

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

const route = useRoute()
const authStore = useAuthStore()

const capsule = ref(null) // Para os dados completos da cápsula
const loading = ref(true)
const error = ref(null)
const checkResult = ref(null) // Para o resultado do /check
const capsuleDate = ref(null) // Para armazenar a data de liberação

const capsuleId = route.params.id

// Função para buscar a localização atual do usuário
const getCurrentLocation = () => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocalização não é suportada pelo seu navegador.'))
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
        // Se o usuário negar, continuamos com lat/lng nulos
        console.warn('Usuário negou geolocalização.', err.message)
        resolve({ lat: null, lng: null })
      }
    )
  })
}

// Função principal para buscar e verificar a cápsula
const fetchCapsule = async () => {
  loading.value = true
  error.value = null
  
  if (!authStore.token) {
    error.value = "Você não está autenticado."
    loading.value = false
    return
  }

  try {
    // 1. Pega a localização do usuário
    const location = await getCurrentLocation()

    // 2. CHAMA O /check para ver se pode abrir
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

    // 3. Se PUDER ABRIR, busca o conteúdo completo
    if (checkResult.value.can_open) {
      const capsuleResponse = await axios.get(
        `${import.meta.env.VITE_API_URL}/capsules/${capsuleId}`,
        {
          headers: { Authorization: `Bearer ${authStore.token}` }
        }
      )
      capsule.value = capsuleResponse.data
    } else {
      // Se não puder abrir, tentamos pegar a data de liberação para mostrar
      // Isso é opcional, mas melhora a UI
      try {
        const capsuleInfo = await axios.get(
          `${import.meta.env.VITE_API_URL}/capsules/${capsuleId}`,
          { headers: { Authorization: `Bearer ${authStore.token}` } }
        )
        capsuleDate.value = capsuleInfo.data.release_date
      } catch (infoError) {
        // Não faz nada se falhar, o motivo do 'check' já é suficiente
      }
    }

  } catch (err) {
    if (err.response) {
      error.value = err.response.data?.error || 'Erro ao buscar cápsula.'
    } else {
      error.value = 'Erro de rede ou servidor indisponível.'
    }
  } finally {
    loading.value = false
  }
}

// Função para formatar data (opcional, mas útil)
const formatDate = (dateString) => {
  if (!dateString) return ''
  const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' }
  return new Date(dateString).toLocaleDateString('pt-BR', options)
}

// Função para o botão "Tentar Novamente"
const reCheck = () => {
  fetchCapsule()
}

// Busca os dados quando o componente é montado
onMounted(() => {
  fetchCapsule()
})
</script>

<style scoped>
.detail-container {
  max-width: 900px;
  margin: 2rem auto;
  padding: 2rem;
  background: #35495e;
  border-radius: 8px;
  color: white;
}

.loading-message, .error-message {
  text-align: center;
}

.error-message h2 {
  color: #e74c3c;
}

.capsule-locked {
  text-align: center;
  padding: 2rem;
  background: rgba(0,0,0,0.2);
  border-radius: 8px;
}
.capsule-locked h2 {
  font-size: 2rem;
}
.recheck-btn {
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}
.recheck-btn:hover {
  background: #3aa876;
}

.capsule-open h2 {
  text-align: center;
  color: #42b983;
  font-size: 2.2rem;
  margin-bottom: 1.5rem;
}

.message-text {
  font-size: 1.2rem;
  line-height: 1.6;
  white-space: pre-wrap; /* Preserva quebras de linha */
  background: rgba(0,0,0,0.1);
  padding: 1rem;
  border-radius: 4px;
}

.media-gallery {
  margin-top: 2rem;
}

.media-gallery h3 {
  border-bottom: 2px solid #42b983;
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

.media-item {
  margin-bottom: 1.5rem;
}

.media-item img,
.media-item video {
  width: 100%;
  max-width: 100%;
  border-radius: 4px;
}

.media-item audio {
  width: 100%;
}

.back-link {
  display: inline-block;
  margin-top: 2rem;
  color: #42b983;
  text-decoration: none;
}
</style>