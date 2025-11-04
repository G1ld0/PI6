<template>
  <div class="register-container">
    
    <div v-if="showSuccessMessage" class="register-form success-message-box">
      <h2>📬 Verifique o seu Email</h2>
      <p>Conta criada com sucesso!</p>
      <p>Enviámos um link de confirmação para <strong>{{ email }}</strong>.</p>
      <p>Por favor, clique no link para ativar a sua conta e poder fazer o login.</p>
    </div>

    <form v-else @submit.prevent="handleSubmit" class="register-form">
      <h2>Criar Conta</h2>
      
      <div class="form-group">
        <label for="email">Email</label>
        <input 
          type="email" 
          id="email" 
          v-model="email" 
          required 
          placeholder="seu@email.com"
        >
      </div>
      
      <div class="form-group">
        <label for="password">Senha</label>
        <input 
          type="password" 
          id="password" 
          v-model="password" 
          required 
          placeholder="••••••••"
          minlength="6"
        >
      </div>

      <div class="form-group">
        <label for="confirmPassword">Confirmar Senha</label>
        <input 
          type="password" 
          id="confirmPassword" 
          v-model="confirmPassword" 
          required 
          placeholder="••••••••"
          minlength="6"
        >
      </div>
      
      <button type="submit" :disabled="isLoading" class="submit-btn">
        {{ isLoading ? 'Criando...' : 'Criar Conta' }}
      </button>
      
      <p v-if="error" class="error-message">{{ error }}</p>
      
      <p class="login-link">
        Já tem uma conta? 
        <router-link to="/login">Faça login</router-link>
      </p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
// [MUDANÇA] Importa a store em vez do supabase direto
import { useAuthStore } from '../stores/auth' 

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref(null)
const isLoading = ref(false)
// [MUDANÇA] Nova ref para a mensagem de sucesso
const showSuccessMessage = ref(false) 

const authStore = useAuthStore()
const router = useRouter() // O router não está a ser usado aqui, mas pode manter

// [MUDANÇA] Lógica de 'handleSubmit' corrigida
const handleSubmit = async () => {
  error.value = null
  isLoading.value = true
  showSuccessMessage.value = false // Reseta a mensagem

  // 1. Verifica se as senhas coincidem
  if (password.value !== confirmPassword.value) {
    error.value = 'As senhas não coincidem.'
    isLoading.value = false
    return
  }

  try {
    // 2. Chama a nova ação 'register' da store
    const success = await authStore.register(email.value, password.value)

    if (success) {
      // 3. Se for bem-sucedido, mostra a mensagem de sucesso
      showSuccessMessage.value = true
    } else {
      // 4. Se falhar, mostra o erro vindo da store
      error.value = authStore.error
    }
  } catch (err) {
    error.value = 'Ocorreu um erro inesperado.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
/* [MUDANÇA] Estilos atualizados para o tema escuro */
.register-container {
  max-width: 450px;
  margin: 3rem auto;
  padding: 2rem;
}

.register-form {
  background: #35495e; /* Fundo escuro do cartão */
  padding: 2.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

h2 {
  text-align: center;
  color: white;
  margin-top: 0;
  margin-bottom: 2rem;
  font-weight: 600;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #c0d0e0; /* Cor do label mais suave */
}

/* Os inputs já são estilizados pelo main.css (fundo escuro, texto claro) */

.submit-btn {
  background: #42b983;
  color: white;
  border: none;
  padding: 0.85rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  width: 100%;
  transition: background-color 0.2s;
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
  text-align: center;
  margin-top: 1rem;
  margin-bottom: 0;
}

.login-link {
  text-align: center;
  margin-top: 1.5rem;
  color: #c0d0e0;
}

.login-link a {
  color: #42b983;
  font-weight: 600;
  text-decoration: none;
}

.login-link a:hover {
  text-decoration: underline;
}

/* [MUDANÇA] Novo estilo para a caixa de sucesso */
.success-message-box {
  text-align: center;
  color: #c0d0e0;
}
.success-message-box h2 {
  color: #42b983;
}
.success-message-box p {
  line-height: 1.6;
}
</style>