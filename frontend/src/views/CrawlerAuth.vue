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

      <!-- 各平台配置状态卡片 -->
      <div class="platform-configs">
        <div
          v-for="p in platforms"
          :key="p.key"
          class="platform-config-card"
          :class="platformCardClass(p.key)"
        >
          <div class="config-card-header">
            <span class="config-platform-icon">{{ p.icon }}</span>
            <h3>{{ p.name }}</h3>
            <span class="config-status-badge" :class="platformCardClass(p.key)">
              {{ platformStatusText(p.key) }}
            </span>
          </div>
          <p v-if="getConfig(p.key)" class="config-meta">
            <span v-if="getConfig(p.key).last_validated_at">
              📅 最后验证：{{ formatDate(getConfig(p.key).last_validated_at) }}
            </span>
            <span v-if="getConfig(p.key).expires_at">
              · 过期时间：{{ formatDate(getConfig(p.key).expires_at) }}
            </span>
          </p>
          <p v-else class="config-meta no-config">
            尚未配置登录态
          </p>
        </div>
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

      <!-- 平台选择 -->
      <div class="platform-selector">
        <button
          :class="['platform-btn', { active: platform === p.key }]"
          v-for="p in platforms"
          :key="p.key"
          @click="switchPlatform(p.key)"
        >
          <span class="platform-icon">{{ p.icon }}</span>
          <span>{{ p.name }}</span>
        </button>
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
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const platforms = [
  { key: 'xiaohongshu', name: '小红书', icon: '📱' },
  { key: 'zhihu', name: '知乎', icon: '💬' },
]

const platform = ref('xiaohongshu')
const cookieValue = ref('')
const loading = ref(false)
const configs = ref({})  // { xiaohongshu: {...}, zhihu: {...} } or empty

const platformName = computed(() => {
  return platform.value === 'xiaohongshu' ? '小红书' : '知乎'
})

const getConfig = (key) => configs.value[key] || null

const platformCardClass = (key) => {
  const cfg = configs.value[key]
  if (!cfg) return 'unconfigured'
  const status = cfg.status
  if (status === 'valid') return 'valid'
  if (status === 'expiring') return 'expiring'
  return 'invalid'
}

const platformStatusText = (key) => {
  const cfg = configs.value[key]
  if (!cfg) return '未配置'
  const map = { valid: '有效', expiring: '即将过期', expired: '已过期', invalid: '已失效' }
  return map[cfg.status] || cfg.status
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

const switchPlatform = (newPlatform) => {
  platform.value = newPlatform
  cookieValue.value = ''
}

const loadAllConfigs = async () => {
  try {
    const response = await axios.get('/api/crawler/auth/configs')
    if (response.data.success) {
      const map = {}
      for (const item of response.data.data) {
        map[item.platform] = item
      }
      configs.value = map
    }
  } catch (error) {
    console.error('查询配置列表失败：', error)
  }
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
      cookie_value: cookieValue.value,
    })

    if (response.data.success) {
      await loadAllConfigs()
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

onMounted(() => {
  loadAllConfigs()
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

/* Platform config status cards */
.platform-configs {
  display: flex;
  gap: 16px;
  margin-bottom: 32px;
}

.platform-config-card {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-left: 4px solid #e5e5e7;
}

.platform-config-card.valid {
  border-left-color: #34C759;
}

.platform-config-card.expiring {
  border-left-color: #FF9500;
}

.platform-config-card.invalid {
  border-left-color: #FF3B30;
}

.platform-config-card.unconfigured {
  border-left-color: #c7c7cc;
}

.config-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.config-card-header h3 {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
  flex: 1;
}

.config-platform-icon {
  font-size: 20px;
}

.config-status-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 12px;
}

.config-status-badge.valid {
  background: #e8f8ed;
  color: #1a7f3a;
}

.config-status-badge.expiring {
  background: #fff3cd;
  color: #b8860b;
}

.config-status-badge.invalid {
  background: #ffe5e5;
  color: #cc2222;
}

.config-status-badge.unconfigured {
  background: #f0f0f2;
  color: #86868b;
}

.config-meta {
  font-size: 12px;
  color: #86868b;
  margin: 0;
}

.config-meta.no-config {
  color: #aeaeb2;
}

/* Platform selector */
.platform-selector {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.platform-btn {
  flex: 1;
  padding: 16px;
  border: 2px solid #e5e5e7;
  border-radius: 12px;
  background: white;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.platform-icon {
  font-size: 20px;
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
</style>
