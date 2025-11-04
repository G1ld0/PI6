<template>
  <div class="home-container">
    <div class="hero">
      <h1>🕰️ Time Capsule</h1>
      <p class="subtitle">Guarde memórias para serem abertas no futuro ou em locais especiais.</p>
      
      <div class="cta-buttons">
        <router-link to="/login" class="cta-button">Entrar</router-link>
        <router-link to="/register" class="cta-button secondary">Registrar</router-link>
      </div>
    </div>
    
    <div class="features">
      <div class="feature">
        <h3>⏳ Cápsulas Temporais</h3>
        <p>Defina uma data futura para liberação e reviva suas memórias.</p>
      </div>
      <div class="feature">
        <h3>📍 Cápsulas Geográficas</h3>
        <p>Determine que a cápsula só possa ser aberta em um local específico.</p>
      </div>
      <div class="feature">
        <h3>🔒 Segurança</h3>
        <p>Suas memórias ficam protegidas e criptografadas até o momento certo.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
// Página inicial não precisa de lógica complexa
</script>

<style scoped>
.home-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
  color: white; /* Texto claro no fundo escuro */
}

.hero {
  padding: 3rem 1rem;
  background: #35495e;
  border-radius: 12px;
  margin-bottom: 3rem;
}

h1 {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: white;
}

.subtitle {
  font-size: 1.25rem;
  margin-bottom: 2.5rem;
  color: #c0d0e0;
}

.cta-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.cta-button {
  padding: 0.75rem 1.5rem;
  background-color: #42b983;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  transition: background-color 0.2s, transform 0.2s;
}

.cta-button:hover {
  background-color: #3aa876;
  transform: translateY(-2px);
}

.cta-button.secondary {
  background-color: #5a7a96;
}
.cta-button.secondary:hover {
  background-color: #4a6580;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.feature {
  background: #35495e;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.feature:hover {
  transform: translateY(-5px);
}

.feature h3 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  color: #42b983;
  font-size: 1.3rem;
}

.feature p {
  color: #c0d0e0;
  line-height: 1.6;
}
</style>