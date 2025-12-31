<template>
  <div class="auth-container">
    <n-card class="auth-card">
      <div class="header">
        <h1>🏆</h1>
        <h2>{{ isLogin ? t('login.welcome_back') : t('login.join_race') }}</h2>
      </div>

      <n-form ref="formRef" :model="model" :rules="rules">
        <n-form-item path="username" :label="t('login.username')">
          <n-input v-model:value="model.username" :placeholder="t('login.trainer_name')" />
        </n-form-item>
        <n-form-item path="password" :label="t('login.password')">
          <n-input
            v-model:value="model.password"
            type="password"
            show-password-on="click"
            :placeholder="t('login.secret_code')"
          />
        </n-form-item>
        <!-- Email optional for now -->
      </n-form>

      <n-button type="primary" block size="large" @click="handleSubmit" :loading="loading">
        {{ isLogin ? t('login.login') : t('login.register') }}
      </n-button>

      <div class="footer">
        <n-button text type="primary" @click="isLogin = !isLogin">
          {{ isLogin ? t('login.need_account') : t('login.have_account') }}
        </n-button>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import { useMessage, NCard, NForm, NFormItem, NInput, NButton } from 'naive-ui'

const router = useRouter()
const auth = useAuthStore()
const message = useMessage()
const { t } = useI18n()

const isLogin = ref(true)
const loading = ref(false)

const model = reactive({
  username: '',
  password: ''
})

const rules = computed(() => ({
  username: { required: true, message: t('login.required'), trigger: 'blur' },
  password: { required: true, message: t('login.required'), trigger: 'blur' }
}))

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
        message.success(t('login.welcome_trainer'))
        router.push('/')
      } else {
        message.error(t('login.invalid_credentials'))
      }
    } else {
      // Register uses JSON
      await auth.register({ username: model.username, password: model.password })
      message.success(t('login.register_success'))
      isLogin.value = true
    }
  } catch (e) {
    message.error(t('login.error_occurred'))
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
