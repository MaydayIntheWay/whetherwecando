<template>
  <div class="report">
    <div class="container" v-if="report">
      <div class="verdict-card" :class="verdictClass">
        <div class="verdict-badge">{{ report.verdict }}</div>
        <h2>{{ verdictTitle }}</h2>
        <p>{{ report.verdict_reason }}</p>
      </div>
      
      <div class="tabs">
        <button 
          v-for="(tab, idx) in tabs" 
          :key="idx"
          :class="{ active: activeTab === idx }"
          @click="activeTab = idx"
        >
          {{ tab }}
        </button>
      </div>
      
      <div class="tab-content">
        <div v-if="activeTab === 0 && report.demand" class="demand-section">
          <div class="score-card">
            <div class="score-value">{{ report.demand.score }}</div>
            <div class="score-label">需求强度分</div>
          </div>
          
          <div class="heatmap" v-if="report.demand_heatmap">
            <h3>平台声量分布</h3>
            <div class="heatmap-bars">
              <div 
                v-for="(count, platform) in report.demand_heatmap" 
                :key="platform"
                class="heatmap-bar"
              >
                <span class="platform-name">{{ platform }}</span>
                <div class="bar" :style="{ width: getHeatmapWidth(count) }"></div>
                <span class="count">{{ count }}</span>
              </div>
            </div>
          </div>
          
          <div class="signals-list">
            <h3>需求信号</h3>
            <div 
              v-for="(signal, idx) in report.demand.signals" 
              :key="idx"
              class="signal-item"
            >
              <div class="signal-header">
                <span class="platform-tag">{{ signal.platform }}</span>
                <span class="emotion-tag" :class="signal.emotion_intensity">
                  {{ signal.emotion_intensity }}
                </span>
              </div>
              <p class="quote">"{{ signal.quote }}"</p>
              <a :href="signal.source_url" target="_blank" class="source-link">
                查看原文 →
              </a>
            </div>
          </div>
        </div>
        
        <div v-if="activeTab === 1 && report.feasibility" class="feasibility-section">
          <div v-if="report.feasibility.competitors.length === 0">
            <p class="empty">数据中未发现竞品讨论</p>
          </div>
          <div 
            v-for="(comp, idx) in report.feasibility.competitors" 
            :key="idx"
            class="competitor-card"
          >
            <h3>{{ comp.name }}</h3>
            <div class="quotes-grid">
              <div class="quotes-col">
                <h4 class="solved">✓ 已解决</h4>
                <div v-for="(q, i) in comp.solved_quotes" :key="i" class="quote-item">
                  <p>"{{ q.quote }}"</p>
                  <a :href="q.source_url" target="_blank">查看原文 →</a>
                </div>
              </div>
              <div class="quotes-col">
                <h4 class="unsolved">✗ 未解决</h4>
                <div v-for="(q, i) in comp.unsolved_quotes" :key="i" class="quote-item">
                  <p>"{{ q.quote }}"</p>
                  <a :href="q.source_url" target="_blank">查看原文 →</a>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="activeTab === 2 && report.differentiation" class="differentiation-section">
          <div 
            v-for="(gap, idx) in report.differentiation.gaps" 
            :key="idx"
            class="gap-card"
          >
            <div class="gap-header">
              <h3>{{ gap.dimension }}</h3>
              <span class="complaint-count">{{ gap.complaint_count }} 条抱怨</span>
            </div>
            <div 
              v-for="(q, i) in gap.representative_quotes" 
              :key="i"
              class="quote-item"
            >
              <p>"{{ q.quote }}"</p>
              <a :href="q.source_url" target="_blank">查看原文 →</a>
            </div>
          </div>
        </div>
        
        <div v-if="activeTab === 3 && report.risks" class="risks-section">
          <div 
            v-for="(risk, idx) in report.risks.risks" 
            :key="idx"
            class="risk-card"
          >
            <div class="risk-header">
              <span class="risk-type">{{ risk.risk_type }}</span>
              <span class="severity" :class="risk.severity">{{ risk.severity }}风险</span>
            </div>
            <p class="risk-desc">{{ risk.description }}</p>
            <div class="evidence">
              <p>"{{ risk.evidence_quote }}"</p>
              <a :href="risk.source_url" target="_blank">查看证据 →</a>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else class="loading">
      <div class="spinner"></div>
      <p>加载报告中...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const taskId = route.params.task_id
const report = ref(null)
const activeTab = ref(0)

const tabs = ['需求可行性', '产品可行性', '市场差异性', '风险清单']

const verdictClass = computed(() => {
  if (!report.value) return ''
  return `verdict-${report.value.verdict.toLowerCase()}`
})

const verdictTitle = computed(() => {
  if (!report.value) return ''
  const titles = {
    'Go': '建议推进',
    'Pivot': '建议调整',
    'Stop': '建议放弃'
  }
  return titles[report.value.verdict] || ''
})

const maxHeatmap = computed(() => {
  if (!report.value?.demand_heatmap) return 1
  return Math.max(...Object.values(report.value.demand_heatmap))
})

function getHeatmapWidth(count) {
  return `${(count / maxHeatmap.value) * 100}%`
}

onMounted(async () => {
  try {
    const res = await fetch(`/api/report/${taskId}`)
    report.value = await res.json()
  } catch (e) {
    console.error('Failed to load report:', e)
  }
})
</script>

<style scoped>
.report {
  min-height: 100vh;
  background: #F5F5F7;
  padding: 20px;
}

.container {
  max-width: 900px;
  margin: 0 auto;
}

.verdict-card {
  background: white;
  border-radius: 16px;
  padding: 40px;
  text-align: center;
  margin-bottom: 30px;
}

.verdict-badge {
  display: inline-block;
  padding: 8px 24px;
  border-radius: 20px;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}

.verdict-go .verdict-badge {
  background: #34C759;
  color: white;
}

.verdict-pivot .verdict-badge {
  background: #FF9500;
  color: white;
}

.verdict-stop .verdict-badge {
  background: #FF3B30;
  color: white;
}

.verdict-card h2 {
  font-size: 28px;
  margin-bottom: 12px;
}

.verdict-card p {
  color: #86868B;
  line-height: 1.6;
}

.tabs {
  display: flex;
  gap: 8px;
  background: white;
  padding: 8px;
  border-radius: 12px;
  margin-bottom: 20px;
}

.tabs button {
  flex: 1;
  padding: 12px;
  border: none;
  background: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #86868B;
  transition: all 0.2s;
}

.tabs button.active {
  background: #007AFF;
  color: white;
}

.tab-content {
  background: white;
  border-radius: 16px;
  padding: 30px;
}

.score-card {
  text-align: center;
  margin-bottom: 30px;
}

.score-value {
  font-size: 64px;
  font-weight: 600;
  color: #007AFF;
}

.score-label {
  color: #86868B;
}

.heatmap h3 {
  margin-bottom: 16px;
}

.heatmap-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.platform-name {
  width: 100px;
  font-size: 14px;
}

.bar {
  height: 24px;
  background: #007AFF;
  border-radius: 4px;
}

.count {
  font-size: 14px;
  color: #86868B;
}

.signals-list h3 {
  margin-bottom: 16px;
}

.signal-item {
  border-left: 3px solid #007AFF;
  padding-left: 16px;
  margin-bottom: 20px;
}

.signal-header {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.platform-tag,
.emotion-tag {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.platform-tag {
  background: #E5E5EA;
}

.emotion-tag.强烈 {
  background: #FF3B30;
  color: white;
}

.emotion-tag.一般 {
  background: #FF9500;
  color: white;
}

.emotion-tag.轻微 {
  background: #34C759;
  color: white;
}

.quote {
  margin-bottom: 8px;
  line-height: 1.6;
}

.source-link {
  color: #007AFF;
  font-size: 14px;
}

.competitor-card {
  margin-bottom: 30px;
}

.quotes-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 16px;
}

.quotes-col h4 {
  margin-bottom: 12px;
}

.quotes-col h4.solved {
  color: #34C759;
}

.quotes-col h4.unsolved {
  color: #FF3B30;
}

.quote-item {
  margin-bottom: 16px;
  padding: 12px;
  background: #F5F5F7;
  border-radius: 8px;
}

.quote-item p {
  margin-bottom: 8px;
  font-size: 14px;
}

.quote-item a {
  color: #007AFF;
  font-size: 12px;
}

.gap-card {
  margin-bottom: 24px;
  padding: 20px;
  background: #F5F5F7;
  border-radius: 12px;
}

.gap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.complaint-count {
  color: #86868B;
  font-size: 14px;
}

.risk-card {
  border-left: 4px solid #FF3B30;
  padding: 20px;
  margin-bottom: 20px;
  background: #FFF5F5;
  border-radius: 0 12px 12px 0;
}

.risk-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}

.risk-type {
  font-weight: 600;
}

.severity {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.severity.高 {
  background: #FF3B30;
  color: white;
}

.severity.中 {
  background: #FF9500;
  color: white;
}

.severity.低 {
  background: #34C759;
  color: white;
}

.risk-desc {
  margin-bottom: 12px;
}

.evidence {
  padding: 12px;
  background: white;
  border-radius: 8px;
}

.evidence p {
  margin-bottom: 8px;
  font-size: 14px;
}

.evidence a {
  color: #007AFF;
  font-size: 12px;
}

.empty {
  color: #86868B;
  text-align: center;
  padding: 40px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #E5E5EA;
  border-top-color: #007AFF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
