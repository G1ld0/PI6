<template>
  <div class="capsules-container">
    <h1>Minhas Cápsulas do Tempo</h1>

    <div v-if="loading" class="loading">
      Carregando...
    </div>

    <div v-else-if="error" class="error-state">
      Erro ao carregar cápsulas: {{ error }}
      <button @click="fetchCapsules" class="retry-btn">Tentar novamente</button>
    </div>

    <div v-else-if="capsules.length === 0" class="empty-state">
      Nenhuma cápsula disponível no momento.
      <router-link to="/create" class="create-link">Criar nova cápsula</router-link>
    </div>

    <div v-else class="capsules-grid">
      <div 
        v-for="capsule in capsules" 
        :key="capsule.id" 
        class="capsule-card"
        @click="goToDetail(capsule)"
      >
        
        <div class="card-image-container">
          <img 
            v-if="capsule.image_url" 
            :src="capsule.image_url" 
            alt="Imagem da cápsula" 
            class="capsule-image"
            @error="handleImageError"
          >
          <div v-else class="media-icon-placeholder">
            <span>🖼️ 📹 🎵</span>
            <p>Contém Mídias</p>
          </div>
        </div>

        <div class="capsule-info">
          <h3>{{ truncateMessage(capsule.message || 'Cápsula de Mídias') }}</h3>
          <p class="date-text">{{ formatDate(capsule.release_date) }}</p>
        </div>

        <div class="capsule-status" :class="statusClass(capsule)">
          {{ statusText(capsule) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { format, isAfter, parseISO } from 'date-fns'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router' // Importa o Router

const authStore = useAuthStore()
const router = useRouter() // Inicializa o Router

const capsules = ref([])
const loading = ref(true)
const error = ref(null)

// Formata a data
const formatDate = (dateString) => {
  if (!dateString) return ''
  return format(parseISO(dateString), 'dd/MM/yyyy HH:mm')
}

// Trunca mensagens longas
const truncateMessage = (msg) => {
  if (!msg) return 'Cápsula de Mídias'
  return msg.length > 50 ? msg.slice(0, 50) + '...' : msg
}

// Fallback para imagens quebradas (útil para links antigos)
const handleImageError = (e) => {
  e.target.style.display = 'none' // Esconde a imagem quebrada
  // Você pode substituir por um placeholder se quiser
  // e.target.src = 'https://placehold.co/600x400?text=Erro'
}

// Busca as cápsulas no backend
const fetchCapsules = async () => {
  try {
    loading.value = true
    error.value = null
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/capsules`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    // Ordena as cápsulas pela data de criação, mais novas primeiro
    capsules.value = response.data.capsules.sort((a, b) => 
      new Date(b.created_at) - new Date(a.created_at)
    )
  } catch (err) {
    error.value = 'Erro ao carregar cápsulas'
  } finally {
    loading.value = false
  }
}

// Verifica se a data de liberação já passou
const isDateAvailable = (capsuleItem) =>
  isAfter(new Date(), parseISO(capsuleItem.release_date))

// Retorna a classe de CSS para o status
const statusClass = (capsuleItem) =>
  isDateAvailable(capsuleItem) ? 'available' : 'locked'

// Retorna o texto de status
const statusText = (capsuleItem) =>
  isDateAvailable(capsuleItem) ? 'Disponível' : 'Bloqueada'

// [MUDANÇA] Navega para a página de detalhes
const goToDetail = (capsuleItem) => {
  router.push(`/capsules/${capsuleItem.id}`)
}

// Busca as cápsulas ao carregar o componente
onMounted(fetchCapsules)
</script>

<style scoped>
.capsules-container {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

h1 {
  color: white;
  text-align: center;
  margin-bottom: 2rem;
}

.loading, .error-state, .empty-state {
  text-align: center;
  padding: 3rem;
  font-size: 1.2rem;
  color: #ccc;
  background: #35495e;
  border-radius: 8px;
}

.create-link, .retry-btn {
  display: inline-block;
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  background-color: #42b983;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-weight: bold;
  border: none;
  cursor: pointer;
}
.error-state {
  color: #e74c3c;
}
.retry-btn {
  background-color: #e74c3c;
}

.capsules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.capsule-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  color: #2c3e50; /* Texto escuro no card claro */
}

.capsule-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.15);
}

.card-image-container {
  width: 100%;
  height: 180px;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.capsule-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.media-icon-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #5a7a96;
}
.media-icon-placeholder span {
  font-size: 2.5rem;
}
.media-icon-placeholder p {
  margin: 0.5rem 0 0;
  font-weight: 500;
}

.capsule-info {
  padding: 1rem;
  flex-grow: 1; /* Faz o conteúdo empurrar o status para baixo */
}

.capsule-info h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
}

.capsule-info .date-text {
  font-size: 0.9rem;
  color: #5a7a96;
  margin: 0;
}

.capsule-status {
  padding: 0.75rem 1rem;
  text-align: center;
  font-weight: 600;
  font-size: 0.9rem;
  border-top: 1px solid #f0f2f5;
}

.capsule-status.available {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.capsule-status.locked {
  background-color: #fff3e0;
  color: #e65100;
}
</style>