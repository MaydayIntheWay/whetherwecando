<template>
  <div class="crawler-auth">
    <nav class="nav-bar">
      <div class="nav-container">
        <router-link to="/" class="nav-logo">Idea验证工具</router-link>
        <div class="nav-links">
          <router-link to="/crawler/auth" class="nav-link active">
            🔧 爬虫配置
          </router-link>
          <router-link to="/crawler/task" class="nav-link">
            📊 爬取任务
          </router-link>
        </div>
      </div>
    </nav>
    
    <div class="auth-container">
      <h1 class="title">爬虫登录态配置</h1>
      <p class="subtitle">配置平台Cookie后，即可开始爬取数据</p>
      
      <div class="platform-selector">
        <button 
          :class="['platform-btn', { active: platform === 'xiaohongshu' }]"
          @click="switchPlatform('xiaohongshu')"
        >
          <span class="platform-icon">📱</span>
          <span>小红书</span>
        </button>
        <button 
          :class="['platform-btn', { active: platform === 'zhihu' }]"
          @click="switchPlatform('zhihu')"
        >
          <span class="platform-icon">💬</span>
          <span>知乎</span>
        </button>
      </div>
      
      <div class="tutorial-card">
        <h3>📋 如何获取{{ platformName }}的Cookie？</h3>
        <p class="tutorial-intro">按照以下步骤操作，即可轻松获取Cookie</p>
        
        <div class="steps">
          <div class="step">
            <div class="step-number">1</div>
            <div class="step-content">
              <h4>打开浏览器开发者工具</h4>
              <p>在电脑上打开{{ platformName }}网站并登录，然后按 <kbd>F12</kbd> 或右键选择"检查"</p>
            </div>
          </div>
          
          <div class="step">
            <div class="step-number">2</div>
            <div class="step-content">
              <h4>切换到 Network（网络）标签</h4>
              <p>在开发者工具顶部，点击"Network"或"网络"标签</p>
              <img src="/2.png" alt="切换到Network标签" class="step-image" />
            </div>
          </div>
          
          <div class="step">
            <div class="step-number">3</div>
            <div class="step-content">
              <h4>刷新页面</h4>
              <p>按 <kbd>F5</kbd> 或 <kbd>Ctrl+R</kbd> 刷新页面，让Network捕获请求</p>
            </div>
          </div>
          
          <div class="step">
            <div class="step-number">4</div>
            <div class="step-content">
              <h4>找到第一个请求</h4>
              <p>在请求列表中点击第一个请求（通常是网站域名）</p>
              <img src="/4.png" alt="找到第一个请求" class="step-image" />
            </div>
          </div>
          
          <div class="step">
            <div class="step-number">5</div>
            <div class="step-content">
              <h4>复制Cookie值</h4>
              <p>在右侧"Headers"（标头）中找到"Cookie"字段，复制整个值</p>
              <img src="/5.png" alt="复制Cookie值" class="step-image" />
              <div class="tip-box">
                <strong>💡 提示：</strong>Cookie值通常很长，确保完整复制，不要遗漏任何字符
              </div>
            </div>
          </div>
          
          <div class="step">
            <div class="step-number">6</div>
            <div class="step-content">
              <h4>粘贴到下方输入框</h4>
              <p>将复制的Cookie粘贴到下方输入框中，点击"提交配置"即可</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="cookie-form">
        <div class="form-group">
          <label>Cookie值 <span class="required">*</span></label>
          <textarea 
            v-model="cookieValue"
            placeholder="请粘贴从浏览器复制的Cookie值..."
            rows="6"
          ></textarea>
          <p class="form-hint">Cookie值很长是正常的，请确保完整粘贴</p>
        </div>
        <button class="submit-btn" @click="submitCookie" :disabled="loading || !cookieValue.trim()">
          <span v-if="loading" class="loading-spinner"></span>
          {{ loading ? '配置中...' : '提交配置' }}
        </button>
      </div>
      
      <div v-if="authStatus" class="status-card" :class="authStatus.status">
        <div class="status-header">
          <span class="status-icon">{{ statusIcon }}</span>
          <h3>登录态状态</h3>
        </div>
        <p class="status-text">
          {{ statusText }}
        </p>
        <p v-if="authStatus.expires_at" class="status-expires">
          <span class="expires-icon">📅</span>
          过期时间：{{ formatDate(authStatus.expires_at) }}
        </p>
        <button v-if="authStatus.status !== 'valid'" class="retry-btn" @click="retryConfig">
          重新配置
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const platform = ref('xiaohongshu')
const cookieValue = ref('')
const loading = ref(false)
const authStatus = ref(null)

const platformName = computed(() => {
  return platform.value === 'xiaohongshu' ? '小红书' : '知乎'
})

const statusIcon = computed(() => {
  if (!authStatus.value) return ''
  const iconMap = {
    valid: '✅',
    expiring: '⚠️',
    expired: '❌',
    invalid: '❌'
  }
  return iconMap[authStatus.value.status] || '❓'
})

const statusText = computed(() => {
  if (!authStatus.value) return ''
  const statusMap = {
    valid: '登录态有效，可以开始爬取数据',
    expiring: '登录态即将过期，建议重新配置',
    expired: '登录态已过期，请重新配置',
    invalid: '登录态无效，请检查配置'
  }
  return statusMap[authStatus.value.status] || authStatus.value.status
})

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const switchPlatform = (newPlatform) => {
  platform.value = newPlatform
  authStatus.value = null
  cookieValue.value = ''
}

const submitCookie = async () => {
  if (!cookieValue.value.trim()) {
    alert('请输入Cookie值')
    return
  }
  
  loading.value = true
  try {
    const response = await axios.post('/api/crawler/auth/config', {
      platform: platform.value,
      login_type: 'cookie',
      cookie_value: cookieValue.value
    })
    
    if (response.data.success) {
      await checkAuthStatus()
      alert('✅ 配置成功！现在可以开始爬取数据了')
    } else {
      alert('❌ 配置失败：' + (response.data.error || '未知错误'))
    }
  } catch (error) {
    const errorMsg = error.response?.data?.error || error.message
    alert('❌ 配置失败：' + errorMsg)
  } finally {
    loading.value = false
  }
}

const checkAuthStatus = async () => {
  try {
    const response = await axios.get(`/api/crawler/auth/status/${platform.value}`)
    if (response.data.success) {
      authStatus.value = response.data.data
    }
  } catch (error) {
    console.error('查询状态失败：', error)
  }
}

const retryConfig = () => {
  authStatus.value = null
  cookieValue.value = ''
}

onMounted(() => {
  checkAuthStatus()
})
</script>

<style scoped>
.crawler-auth {
  min-height: 100vh;
  background: #f5f5f7;
  padding: 0;
}

.nav-bar {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 0 20px;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 56px;
}

.nav-logo {
  font-size: 18px;
  font-weight: 600;
  color: #1d1d1f;
  text-decoration: none;
}

.nav-links {
  display: flex;
  gap: 24px;
}

.nav-link {
  font-size: 14px;
  font-weight: 500;
  color: #1d1d1f;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.2s;
}

.nav-link:hover {
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
}

.nav-link.active {
  background: rgba(0, 122, 255, 0.1);
  color: #007AFF;
}

.auth-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 0 20px;
}

.title {
  font-size: 32px;
  font-weight: 600;
  text-align: center;
  margin-bottom: 8px;
  color: #1d1d1f;
}

.subtitle {
  text-align: center;
  color: #86868b;
  margin-bottom: 40px;
  font-size: 16px;
}

.platform-selector {
  display: flex;
  gap: 16px;
  margin-bottom: 32px;
}

.platform-btn {
  flex: 1;
  padding: 20px;
  border: 2px solid #e5e5e7;
  border-radius: 16px;
  background: white;
  font-size: 18px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.platform-icon {
  font-size: 24px;
}

.platform-btn.active {
  border-color: #007AFF;
  background: linear-gradient(135deg, #007AFF 0%, #0051D5 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
}

.tutorial-card {
  background: white;
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.tutorial-card h3 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #1d1d1f;
}

.tutorial-intro {
  color: #86868b;
  margin-bottom: 24px;
  font-size: 15px;
}

.steps {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.step {
  display: flex;
  gap: 16px;
}

.step-number {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #007AFF 0%, #0051D5 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 16px;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
}

.step-content h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #1d1d1f;
}

.step-content p {
  color: #6e6e73;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
}

kbd {
  background: #f5f5f7;
  border: 1px solid #d2d2d7;
  border-radius: 4px;
  padding: 2px 8px;
  font-family: monospace;
  font-size: 13px;
}

.step-image {
  width: 100%;
  max-width: 600px;
  border-radius: 8px;
  margin-top: 12px;
  margin-bottom: 12px;
  border: 1px solid #e5e5e7;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tip-box {
  background: #fff3cd;
  border-left: 4px solid #FF9500;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
}

.cookie-form {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #1d1d1f;
}

.required {
  color: #FF3B30;
}

.form-group textarea {
  width: 100%;
  padding: 14px;
  border: 2px solid #e5e5e7;
  border-radius: 12px;
  font-size: 14px;
  resize: vertical;
  font-family: monospace;
  transition: border-color 0.2s;
}

.form-group textarea:focus {
  outline: none;
  border-color: #007AFF;
}

.form-hint {
  margin-top: 8px;
  font-size: 13px;
  color: #86868b;
}

.submit-btn {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #007AFF 0%, #0051D5 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
}

.submit-btn:disabled {
  background: #c7c7cc;
  cursor: not-allowed;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.status-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  margin-top: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.status-card.valid {
  border-left: 4px solid #34C759;
}

.status-card.expiring {
  border-left: 4px solid #FF9500;
}

.status-card.expired,
.status-card.invalid {
  border-left: 4px solid #FF3B30;
}

.status-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.status-icon {
  font-size: 24px;
}

.status-header h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.status-text {
  font-size: 15px;
  color: #6e6e73;
  margin-bottom: 8px;
}

.status-expires {
  font-size: 14px;
  color: #86868b;
  display: flex;
  align-items: center;
  gap: 8px;
}

.expires-icon {
  font-size: 16px;
}

.retry-btn {
  margin-top: 16px;
  padding: 10px 20px;
  background: #007AFF;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #0051D5;
}
</style>
