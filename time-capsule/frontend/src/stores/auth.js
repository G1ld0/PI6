import { defineStore } from 'pinia'
import { supabase } from '../composables/useSupabase'
import axios from 'axios'
// 'useRouter' não é usado aqui, pode ser removido
// import { useRouter } from 'vue-router'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    // [MUDANÇA AQUI] Inicializamos o estado direto do localStorage
    user: null, // O objeto 'user' completo do Supabase
    token: localStorage.getItem('authToken') || null, // Nosso token JWT do backend
    userId: localStorage.getItem('authUserId') || null, // O ID do usuário (UUID)
    isLoading: false,
    error: null
  }),

  // [MUDANÇA AQUI] Adicionamos 'getters' para facilitar
  getters: {
    isAuthenticated: (state) => !!state.token,
    // Isso garante que os componentes sempre possam pegar o ID
    getUserId: (state) => state.userId 
  },

  actions: {
    async login(email, password) {
      try {
        this.isLoading = true
        this.error = null
        
        // 1. Autentica no Supabase
        const { data: supabaseData, error: supabaseError } = await supabase.auth.signInWithPassword({
          email,
          password
        })
        
        if (supabaseError) throw supabaseError
    
        // 2. Obtém token JWT do nosso backend
        const response = await axios.post(
          `${import.meta.env.VITE_API_URL}/login`, 
          { email, password },
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        )
    
        if (!response.data.access_token) {
          throw new Error('Token não recebido do backend')
        }
    
        // [MUDANÇA AQUI] Salvamos no estado
        this.user = supabaseData.user
        this.token = response.data.access_token
        this.userId = response.data.user_id // <-- Importante
        
        // [MUDANÇA AQUI] E também salvamos no localStorage
        localStorage.setItem('authToken', this.token)
        localStorage.setItem('authUserId', this.userId)
        
        return true
      } catch (error) {
        console.error('Erro no login:', error)
        this.error = error.response?.data?.error || 
                       error.message || 
                       'Erro ao conectar com o servidor'
        return false
      } finally {
        this.isLoading = false
      }
    },

    // [NOVA FUNÇÃO DE REGISTO - PASSO 5]
    // Esta é a nova função que você deve adicionar
    async register(email, password) {
      this.isLoading = true
      this.error = null
      
      try {
        // 1. Dizemos ao Supabase para onde redirecionar o utilizador
        //    APÓS ele clicar no link do email.
        const redirectTo = `${window.location.origin}/email-confirmed`

        // 2. Tenta criar o novo usuário no Supabase
        const { data, error: signUpError } = await supabase.auth.signUp({
          email,
          password,
          options: {
            redirectTo: redirectTo // Nome correto é 'redirectTo'
          }
        })

        if (signUpError) throw signUpError

        // 3. NÃO fazemos mais o login. Apenas retornamos sucesso.
        // O utilizador terá de confirmar o email primeiro.
        return true

      } catch (error) {
        console.error('Erro no registo:', error)
        if (error.message.includes("User already registered")) {
            this.error = "Este email já está registado."
        } else {
            this.error = error.response?.data?.error || 
                       error.message || 
                       'Erro ao criar a conta'
        }
        return false
      } finally {
        this.isLoading = false
      }
    },
    // [FIM DA NOVA FUNÇÃO]

    async logout() {
      try {
        await supabase.auth.signOut()
        
        // [MUDANÇA AQUI] Limpamos o estado
        this.user = null
        this.token = null
        this.userId = null
        
        // [MUDANÇA AQUI] E também limpamos o localStorage
        localStorage.removeItem('authToken')
        localStorage.removeItem('authUserId')
        
      } catch (error) {
        console.error('Erro no logout:', error)
      }
    },

    async checkAuth() {
      // Esta função agora serve para 'hidratar' o objeto 'user'
      // e verificar if a sessão do Supabase ainda é válida.
      // O token e o userId já foram carregados no 'state'.
      try {
        const { data } = await supabase.auth.getUser()
        this.user = data.user
        
        // Se a sessão do Supabase expirou, mas tínhamos tokens locais,
        // força um logout completo para limpar tudo.
        if (!data.user && this.token) {
          this.logout()
        }
      } catch (error) {
        this.user = null
        this.logout() // Força o logout se houver erro
      }
    }
  }
})