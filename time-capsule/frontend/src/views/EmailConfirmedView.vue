<template>
  <div class="confirm-container">
    <div class="confirm-box">
      <h2>🎉 Sucesso!</h2>
      <p>O seu email foi confirmado com sucesso.</p>
      <p>Agora você já pode fazer o login e começar a criar as suas cápsulas do tempo.</p>
      <router-link to="/login" class="login-btn">Ir para o Login</router-link>
    </div>
  </div>
</template>

<script setup>
// Esta página é apenas visual, o Supabase trata da confirmação
// em segundo plano assim que o utilizador a carrega.
</script>

<style scoped>
.confirm-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
  min-height: 70vh;
}
.confirm-box {
  background: #35495e;
  padding: 2.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  text-align: center;
  max-width: 500px;
  color: #c0d0e0;
}
h2 {
  color: #42b983;
  margin-top: 0;
  font-size: 2rem;
}
p {
  font-size: 1.1rem;
  line-height: 1.6;
}
.login-btn {
  display: inline-block;
  margin-top: 1.5rem;
  background: #42b983;
  color: white;
  border: none;
  padding: 0.85rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  text-decoration: none;
  transition: background-color 0.2s;
}
.login-btn:hover {
  background: #3aa876;
}
</style>