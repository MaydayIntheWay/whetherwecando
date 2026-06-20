<template>
  <div class="validating">
    <div class="container">
      <div class="progress-card">
        <div class="spinner" :class="{ indeterminate: currentStep === 0 && !error }"></div>

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
          <p class="phase-message">{{ phaseMessage }}</p>
          <p v-if="crawlCount > 0" class="crawl-count">
            已抓取 <strong>{{ crawlCount }}</strong> 条数据
          </p>
          <p class="elapsed-time">{{ elapsedText }}</p>
        </div>

        <div class="progress-bar" :class="{ indeterminate: currentStep === 0 && crawlCount === 0 }">
          <div class="progress-fill" :style="{ width: progressWidth }"></div>
        </div>

        <p v-if="crawlCount === 0 && currentStep === 0" class="hint">
          首次抓取约需 5-10 分钟，数据正在实时获取中...
        </p>

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
const elapsedSeconds = ref(0)
let eventSource = null
let elapsedTimer = null
let messageTimer = null

const steps = [
  '数据抓取',
  'AI 分析',
  '生成报告',
]

const crawlingPhrases = [
  '正在启动浏览器...',
  '正在搜索关键词...',
  '正在解析内容...',
  '数据采集中，请耐心等待...',
]

const phraseIndex = ref(0)

const phaseMessage = computed(() => {
  if (error.value) return ''
  if (currentStep.value === 1) return '正在使用 AI 分析数据...'
  if (currentStep.value === 2) return '正在生成验证报告...'
  if (crawlCount.value > 0) return `正在抓取数据...已抓取 ${crawlCount.value} 条`
  return crawlingPhrases[phraseIndex.value] || '准备中...'
})

const progressWidth = computed(() => {
  if (currentStep.value === 0 && crawlCount.value === 0) return '30%'
  return `${((currentStep.value + 1) / steps.length) * 100}%`
})

const elapsedText = computed(() => {
  const mins = Math.floor(elapsedSeconds.value / 60)
  const secs = elapsedSeconds.value % 60
  if (mins > 0) return `已等待 ${mins} 分 ${secs} 秒`
  return `已等待 ${secs} 秒`
})

onMounted(() => {
  connectSSE()
  startTimers()
})

onUnmounted(() => {
  if (eventSource) eventSource.close()
  if (elapsedTimer) clearInterval(elapsedTimer)
  if (messageTimer) clearInterval(messageTimer)
})

function startTimers() {
  elapsedTimer = setInterval(() => {
    elapsedSeconds.value++
  }, 1000)
  messageTimer = setInterval(() => {
    phraseIndex.value = (phraseIndex.value + 1) % crawlingPhrases.length
  }, 3000)
}

function stopTimers() {
  if (elapsedTimer) { clearInterval(elapsedTimer); elapsedTimer = null }
  if (messageTimer) { clearInterval(messageTimer); messageTimer = null }
}

function connectSSE() {
  eventSource = new EventSource(`/api/validate/stream?task_id=${taskId}`)

  eventSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)

      if (data.stage === 'done') {
        stopTimers()
        eventSource.close()
        router.push(`/report/${taskId}`)
      } else if (data.stage === 'error') {
        stopTimers()
        error.value = data.message || '验证失败'
        eventSource.close()
      } else if (data.stage === 'crawling') {
        currentStep.value = 0
        crawlCount.value = data.count || 0
        currentMessage.value = data.message || ''
      } else if (data.stage === 'analyzing') {
        stopTimers()
        currentStep.value = 1
      }
    } catch (err) {
      console.error('SSE parse error:', err)
    }
  }

  eventSource.onerror = () => {
    stopTimers()
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

.spinner.indeterminate {
  width: 56px;
  height: 56px;
  border-width: 4px;
  border-color: #E5E5EA;
  border-top-color: #007AFF;
  animation: spin 0.8s linear infinite;
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

.phase-message {
  color: #333;
  font-size: 15px;
  min-height: 22px;
}

.crawl-count {
  color: #007AFF;
  font-size: 16px;
  margin-top: 8px;
}

.elapsed-time {
  color: #86868B;
  font-size: 13px;
  margin-top: 6px;
}

.progress-bar {
  height: 4px;
  background: #E5E5EA;
  border-radius: 2px;
  overflow: hidden;
  position: relative;
}

.progress-bar.indeterminate {
  background: transparent;
}

.progress-bar.indeterminate::before {
  content: '';
  position: absolute;
  top: 0;
  height: 100%;
  width: 40%;
  background: #007AFF;
  border-radius: 2px;
  animation: indeterminate-slide 1.5s ease-in-out infinite;
}

@keyframes indeterminate-slide {
  0% { left: -40%; }
  100% { left: 100%; }
}

.progress-fill {
  height: 100%;
  background: #007AFF;
  transition: width 0.5s ease;
}

.hint {
  color: #86868B;
  font-size: 13px;
  margin-top: 16px;
}

.error {
  color: #FF3B30;
  margin-top: 20px;
}
</style>
