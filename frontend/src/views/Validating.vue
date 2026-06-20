<template>
  <div class="validating">
    <div class="container">
      <div class="progress-card">
        <div class="spinner"></div>
        
        <h2>正在验证中...</h2>
        
        <div class="progress-steps">
          <div 
            v-for="(step, idx) in steps" 
            :key="idx"
            class="step"
            :class="{ active: currentStep === idx, done: currentStep > idx }"
          >
            <div class="step-icon">
              <span v-if="currentStep > idx">✓</span>
              <span v-else>{{ idx + 1 }}</span>
            </div>
            <span class="step-text">{{ step }}</span>
          </div>
        </div>
        
        <div class="progress-detail">
          <p>{{ currentMessage || '准备中...' }}</p>
          <p v-if="crawlCount > 0" class="crawl-count">
            已抓取 <strong>{{ crawlCount }}</strong> 条数据
          </p>
        </div>
        
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressWidth }"></div>
        </div>
        
        <p v-if="error" class="error">{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const taskId = route.params.task_id
const currentStep = ref(0)
const crawlCount = ref(0)
const currentMessage = ref('')
const error = ref('')
let eventSource = null

const steps = [
  '数据抓取',
  'AI 分析',
  '生成报告',
]

const progressWidth = computed(() => {
  return `${((currentStep.value + 1) / steps.length) * 100}%`
})

onMounted(() => {
  connectSSE()
})

onUnmounted(() => {
  if (eventSource) {
    eventSource.close()
  }
})

function connectSSE() {
  eventSource = new EventSource(`/api/validate/stream?task_id=${taskId}`)
  
  eventSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      
      if (data.stage === 'done') {
        eventSource.close()
        router.push(`/report/${taskId}`)
      } else if (data.stage === 'error') {
        error.value = data.message || '验证失败'
        eventSource.close()
      } else if (data.stage === 'crawling') {
        currentStep.value = 0
        crawlCount.value = data.count || 0
        currentMessage.value = data.message || ''
      } else if (data.stage === 'analyzing') {
        currentStep.value = 1
        currentMessage.value = '正在使用 AI 分析数据...'
      }
    } catch (err) {
      console.error('SSE parse error:', err)
    }
  }
  
  eventSource.onerror = () => {
    error.value = '连接中断，请刷新页面重试'
    eventSource.close()
  }
}
</script>

<style scoped>
.validating {
  min-height: 100vh;
  background: #F5F5F7;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.container {
  width: 100%;
  max-width: 600px;
}

.progress-card {
  background: white;
  border-radius: 16px;
  padding: 40px;
  text-align: center;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 3px solid #E5E5EA;
  border-top-color: #007AFF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

h2 {
  font-size: 24px;
  margin-bottom: 30px;
}

.progress-steps {
  display: flex;
  justify-content: space-between;
  margin-bottom: 30px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.step-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #E5E5EA;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #86868B;
  transition: all 0.3s;
}

.step.active .step-icon {
  background: #007AFF;
  color: white;
}

.step.done .step-icon {
  background: #34C759;
  color: white;
}

.step-text {
  font-size: 12px;
  color: #86868B;
}

.step.active .step-text {
  color: #007AFF;
}

.progress-detail {
  margin-bottom: 20px;
}

.progress-detail p {
  color: #86868B;
}

.progress-bar {
  height: 4px;
  background: #E5E5EA;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #007AFF;
  transition: width 0.3s;
}

.crawl-count {
  color: #007AFF;
  font-size: 16px;
  margin-top: 8px;
}

.error {
  color: #FF3B30;
  margin-top: 20px;
}
</style>
