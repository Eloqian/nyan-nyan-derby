import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface User {
  id: string
  username: string
  email?: string
  is_admin: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => !!user.value?.is_admin)

  async function login(formData: FormData) {
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        body: formData, // Sending form data
      })
      if (!res.ok) throw new Error('Login failed')
      
      const data = await res.json()
      token.value = data.access_token
      localStorage.setItem('token', data.access_token)
      await fetchUser()
      return true
    } catch (e) {
      console.error(e)
      return false
    }
  }

  async function register(jsonBody: any) {
     const res = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(jsonBody)
     })
     if (!res.ok) throw new Error('Registration failed')
     return true
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const res = await fetch('/api/v1/auth/me', {
        headers: { 'Authorization': `Bearer ${token.value}` }
      })
      if (res.ok) {
        user.value = await res.json()
      } else {
        logout()
      }
    } catch (e) {
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    // Optionally redirect
  }

  return { token, user, isAuthenticated, isAdmin, login, register, fetchUser, logout }
})
