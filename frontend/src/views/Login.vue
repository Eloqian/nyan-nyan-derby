<template>
  <div class="auth-container">
    <n-card class="auth-card">
      <div class="header">
        <h1>🏆</h1>
        <h2>{{ isLogin ? 'Welcome Back' : 'Join the Race' }}</h2>
      </div>

      <n-form ref="formRef" :model="model" :rules="rules">
        <n-form-item path="username" label="Username">
          <n-input v-model:value="model.username" placeholder="Trainer Name" />
        </n-form-item>
        <n-form-item path="password" label="Password">
          <n-input
            v-model:value="model.password"
            type="password"
            show-password-on="click"
            placeholder="Secret Code"
          />
        </n-form-item>
        <!-- Email optional for now -->
      </n-form>

      <n-button type="primary" block size="large" @click="handleSubmit" :loading="loading">
        {{ isLogin ? 'Login' : 'Register' }}
      </n-button>

      <div class="footer">
        <n-button text type="primary" @click="isLogin = !isLogin">
          {{ isLogin ? 'Need an account? Register' : 'Already have an account? Login' }}
        </n-button>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useMessage, NCard, NForm, NFormItem, NInput, NButton } from 'naive-ui'

const router = useRouter()
const auth = useAuthStore()
const message = useMessage()

const isLogin = ref(true)
const loading = ref(false)

const model = reactive({
  username: '',
  password: ''
})

const rules = {
  username: { required: true, message: 'Required', trigger: 'blur' },
  password: { required: true, message: 'Required', trigger: 'blur' }
}

const handleSubmit = async () => {
  loading.value = true
  try {
    if (isLogin.value) {
      // Login uses OAuth2 Form Data
      const formData = new FormData()
      formData.append('username', model.username)
      formData.append('password', model.password)
      
      const success = await auth.login(formData)
      if (success) {
        message.success('Welcome back, Trainer!')
        router.push('/')
      } else {
        message.error('Invalid credentials')
      }
    } else {
      // Register uses JSON
      await auth.register({ username: model.username, password: model.password })
      message.success('Registration successful! Please login.')
      isLogin.value = true
    }
  } catch (e) {
    message.error('An error occurred')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
}
.auth-card {
  width: 100%;
  max-width: 400px;
  padding: 20px;
}
.header {
  text-align: center;
  margin-bottom: 20px;
}
.header h1 {
  font-size: 48px;
  margin: 0;
}
.footer {
  margin-top: 16px;
  text-align: center;
}
</style>
