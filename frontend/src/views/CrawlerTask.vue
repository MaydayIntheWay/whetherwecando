<template>
  <div class="crawler-task">
    <nav class="nav-bar">
      <div class="nav-container">
        <router-link to="/" class="nav-logo">Idea验证工具</router-link>
        <div class="nav-links">
          <router-link to="/crawler/auth" class="nav-link">
            🔧 爬虫配置
          </router-link>
          <router-link to="/crawler/task" class="nav-link active">
            📊 爬取任务
          </router-link>
        </div>
      </div>
    </nav>
    
    <div class="task-container">
      <h1 class="title">爬取任务</h1>
      
      <div class="form-section">
        <div class="form-group">
          <label>选择平台</label>
          <div class="platform-selector">
            <button 
              :class="['platform-btn', { active: platform === 'xiaohongshu' }]"
              @click="platform = 'xiaohongshu'"
            >
              小红书
            </button>
            <button 
              :class="['platform-btn', { active: platform === 'zhihu' }]"
              @click="platform = 'zhihu'"
            >
              知乎
            </button>
          </div>
        </div>
        
        <div class="form-group">
          <label>搜索关键词</label>
          <input 
            v-model="keyword"
            type="text"
            placeholder="请输入关键词..."
          />
        </div>
        
        <div class="form-group">
          <label>爬取数量（1-100）</label>
          <input 
            v-model.number="maxCount"
            type="number"
            min="1"
            max="100"
          />
        </div>
        
        <button class="submit-btn" @click="startCrawl" :disabled="loading">
          {{ loading ? '爬取中...' : '开始爬取' }}
        </button>
      </div>
      
      <div v-if="progress" class="progress-section">
        <h3>爬取进度</h3>
        <div class="progress-bar">
          <div 
            class="progress-fill"
            :style="{ width: progressPercent + '%' }"
          ></div>
        </div>
        <p class="progress-text">
          {{ progress.current }} / {{ progress.total }}
          <span v-if="progress.message"> - {{ progress.message }}</span>
        </p>
      </div>
      
      <div v-if="results.length > 0" class="results-section">
        <h3>爬取结果（{{ results.length }}条）</h3>
        <div class="results-list">
          <div 
            v-for="(item, index) in results"
            :key="index"
            class="result-item"
          >
            <div class="result-header">
              <span class="result-platform">{{ item.platform }}</span>
              <span class="result-engagement">互动量：{{ item.engagement }}</span>
              <span :class="['result-emotion', item.emotion_intensity]">
                {{ item.emotion_intensity }}
              </span>
            </div>
            <p class="result-content">{{ item.content }}</p>
            <a 
              :href="item.source_url"
              target="_blank"
              class="result-link"
            >
              查看原文 →
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'

const platform = ref('xiaohongshu')
const keyword = ref('')
const maxCount = ref(50)
const loading = ref(false)
const progress = ref(null)
const results = ref([])

const progressPercent = computed(() => {
  if (!progress.value || progress.value.total === 0) return 0
  return Math.round((progress.value.current / progress.value.total) * 100)
})

const startCrawl = async () => {
  if (!keyword.value.trim()) {
    alert('请输入关键词')
    return
  }
  
  loading.value = true
  results.value = []
  progress.value = null
  
  try {
    const response = await axios.post('/api/crawler/crawl', {
      platform: platform.value,
      keyword: keyword.value,
      max_count: maxCount.value
    })
    
    if (response.data.success) {
      const data = response.data.data
      results.value = data.items || []
      progress.value = {
        current: data.success,
        total: data.total,
        message: '爬取完成'
      }
    } else {
      alert('爬取失败：' + response.data.error)
    }
  } catch (error) {
    alert('爬取失败：' + (error.response?.data?.error || error.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.crawler-task {
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

.task-container {
  max-width: 800px;
  margin: 40px auto 0;
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.title {
  font-size: 28px;
  font-weight: 600;
  text-align: center;
  margin-bottom: 30px;
  color: #1d1d1f;
}

.form-section {
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #1d1d1f;
}

.platform-selector {
  display: flex;
  gap: 12px;
}

.platform-btn {
  flex: 1;
  padding: 12px 20px;
  border: 2px solid #e5e5e7;
  border-radius: 12px;
  background: white;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.platform-btn.active {
  border-color: #007AFF;
  background: #007AFF;
  color: white;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 1px solid #e5e5e7;
  border-radius: 12px;
  font-size: 16px;
}

.submit-btn {
  width: 100%;
  padding: 14px;
  background: #007AFF;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.submit-btn:hover {
  background: #0051D5;
}

.submit-btn:disabled {
  background: #c7c7cc;
  cursor: not-allowed;
}

.progress-section {
  margin-bottom: 30px;
  padding: 20px;
  background: #f5f5f7;
  border-radius: 12px;
}

.progress-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e5e5e7;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: #007AFF;
  transition: width 0.3s;
}

.progress-text {
  font-size: 14px;
  color: #6e6e73;
}

.results-section {
  margin-top: 30px;
}

.results-section h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-item {
  padding: 20px;
  background: #f5f5f7;
  border-radius: 12px;
}

.result-header {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 14px;
}

.result-platform {
  padding: 4px 8px;
  background: #007AFF;
  color: white;
  border-radius: 6px;
  font-weight: 500;
}

.result-engagement {
  color: #6e6e73;
}

.result-emotion {
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: 500;
}

.result-emotion.strong {
  background: #FF3B30;
  color: white;
}

.result-emotion.medium {
  background: #FF9500;
  color: white;
}

.result-emotion.weak {
  background: #34C759;
  color: white;
}

.result-content {
  font-size: 14px;
  line-height: 1.6;
  color: #1d1d1f;
  margin-bottom: 12px;
}

.result-link {
  font-size: 14px;
  color: #007AFF;
  text-decoration: none;
  font-weight: 500;
}

.result-link:hover {
  text-decoration: underline;
}
</style>
