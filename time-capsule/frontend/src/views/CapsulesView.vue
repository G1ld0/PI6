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
            v-if="getCapsuleStatus(capsule) === 'available' && capsule.image_url" 
            :src="capsule.image_url" 
            alt="Imagem da cápsula" 
            class="capsule-image"
            @error="handleImageError"
          >
          <div v-else class="media-icon-placeholder">
            <span v-if="getCapsuleStatus(capsule) === 'locked_location'">🔒</span>
            <span v-else-if="capsule.tipo === 'fisica'">🤖</span> <span v-else-if="getCapsuleStatus(capsule) === 'available' && !capsule.image_url">🖼️ 📹 🎵</span>
            <span v-else>⏳</span>
            
            <p v-if="getCapsuleStatus(capsule) === 'locked_location'">Requer Localização</p>
            <p v-else-if="capsule.tipo === 'fisica'">Cápsula Física (IoT)</p> <p v-else-if="getCapsuleStatus(capsule) === 'available' && !capsule.image_url">Contém Mídias</p>
            <p v-else>Bloqueada</p>
          </div>
        </div>

        <div class="capsule-info">
          <h3>{{ truncateMessage(capsule.message || 'Cápsula de Mídias') }}</h3>
          <p class="date-text">{{ formatDate(capsule.release_date) }}</p>

          <span 
            class="capsule-type-badge" 
            :class="capsule.tipo === 'fisica' ? 'iot' : 'digital'"
          >
            {{ capsule.tipo === 'fisica' ? 'Física (IoT)' : 'Digital' }}
          </span>
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
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const capsules = ref([])
const loading = ref(true)
const error = ref(null)

const formatDate = (dateString) => {
  if (!dateString) return ''
  return format(parseISO(dateString), 'dd/MM/yyyy HH:mm')
}

const truncateMessage = (msg) => {
  if (!msg) return 'Cápsula de Mídias'
  return msg.length > 50 ? msg.slice(0, 50) + '...' : msg
}

const handleImageError = (e) => {
  e.target.style.display = 'none'
}

const fetchCapsules = async () => {
  try {
    loading.value = true
    error.value = null
    const response = await axios.get(`${import.meta.env.VITE_API_URL}/capsules`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    // Agora o 'response.data.capsules' já inclui o campo 'tipo'
    capsules.value = response.data.capsules.sort((a, b) => 
      new Date(b.created_at) - new Date(a.created_at)
    )
  } catch (err) {
    error.value = 'Erro ao carregar cápsulas'
  } finally {
    loading.value = false
  }
}

const getCapsuleStatus = (capsule) => {
  // A data de 'release_date' vem como string ISO (ex: "2025-11-05T14:00:00")
  // Precisamos convertê-la para um objeto Date para comparar.
  const releaseDate = parseISO(capsule.release_date);
  const dateHasPassed = isAfter(new Date(), releaseDate);
  const hasLocation = capsule.lat !== null && capsule.lng !== null;

  if (!dateHasPassed) {
    return 'locked_date'; // Bloqueada (Data)
  }
  if (hasLocation) {
    return 'locked_location'; // Bloqueada (Localização)
  }
  return 'available'; // Disponível
}

const statusClass = (capsule) => {
  const status = getCapsuleStatus(capsule);
  return (status === 'available') ? 'available' : 'locked';
}

const statusText = (capsule) => {
  const status = getCapsuleStatus(capsule);
  if (status === 'locked_date') return 'Bloqueada';
  if (status === 'locked_location') return 'Requer Localização';
  return 'Disponível';
}

const goToDetail = (capsuleItem) => {
  router.push(`/capsules/${capsuleItem.id}`)
}

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
  color: #2c3e50;
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
  border-bottom: 1px solid #e0e0e0;
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
  text-align: center;
  padding: 1rem;
}
.media-icon-placeholder span {
  font-size: 2.5rem;
}
.media-icon-placeholder p {
  margin: 0.5rem 0 0;
  font-weight: 600;
  font-size: 0.9rem;
}

.capsule-info {
  padding: 1rem;
  flex-grow: 1; 
}

.capsule-info h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
}

.capsule-info .date-text {
  font-size: 0.9rem;
  color