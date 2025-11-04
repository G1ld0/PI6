<template>
  <div ref="mapContainer" class="map-display"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// [A CORREÇÃO ESTÁ AQUI] Importa as imagens dos marcadores
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

// Define as propriedades do componente (lat e lng)
const props = defineProps({
  lat: {
    type: Number,
    required: true
  },
  lng: {
    type: Number,
    required: true
  }
})

// Ref para o elemento <div> do mapa
const mapContainer = ref(null)
let mapInstance = null

// [A CORREÇÃO ESTÁ AQUI] Sobrescreve os caminhos dos ícones do Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
})

// 'onMounted' é chamado quando o componente é renderizado na tela
onMounted(() => {
  if (mapContainer.value) {
    // Cria a instância do mapa
    mapInstance = L.map(mapContainer.value).setView([props.lat, props.lng], 15) // Zoom 15

    // Adiciona o "chão" do mapa (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(mapInstance)

    // Adiciona o marcador (o pino)
    L.marker([props.lat, props.lng]).addTo(mapInstance)
  }
})

// 'onUnmounted' é chamado quando o componente é destruído
// Isso previne que o mapa continue existindo em memória
onUnmounted(() => {
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }
})
</script>

<style scoped>
.map-display {
  width: 100%;
  height: 100%; /* O componente pai (CapsuleDetailView) define a altura */
  border-radius: 8px;
  z-index: 1; /* Garante que o mapa fique acima do fundo */
}
</style>