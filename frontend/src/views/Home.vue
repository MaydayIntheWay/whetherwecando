<template>
  <div class="home">
    <div class="container">
      <h1 class="title">Idea 可行性验证工具</h1>
      <p class="subtitle">验证你的产品创意是否值得投入</p>
      
      <div class="entry-cards">
        <div 
          class="card" 
          :class="{ active: mode === 'idea' }"
          @click="switchMode('idea')"
        >
          <div class="card-icon">💡</div>
          <h3>描述灵感</h3>
          <p>用自然语言描述你的想法</p>
        </div>
        
        <div 
          class="card"
          :class="{ active: mode === 'form' }"
          @click="switchMode('form')"
        >
          <div class="card-icon">📝</div>
          <h3>填写表单</h3>
          <p>结构化输入产品信息</p>
        </div>
      </div>
      
      <div v-if="mode === 'idea'" class="idea-input">
        <textarea 
          v-model="rawIdea"
          placeholder="描述你的产品灵感，例如：我想做一个帮助独立开发者验证产品想法的工具..."
          rows="6"
        ></textarea>
        <button 
          class="btn-primary"
          @click="submitIdea"
          :disabled="!rawIdea.trim() || loading"
        >
          {{ loading ? '提取中...' : '提炼关键词' }}
        </button>
      </div>
      
      <div v-if="mode === 'form'" class="form-input">
        <div class="form-group">
          <label>痛点描述 <span class="required">*</span></label>
          <textarea 
            v-model="form.problem"
            placeholder="用户遇到了什么问题？"
            rows="3"
          ></textarea>
        </div>
        
        <div class="form-group">
          <label>解决方案 <span class="required">*</span></label>
          <textarea 
            v-model="form.solution"
            placeholder="你打算怎么解决？"
            rows="3"
          ></textarea>
        </div>
        
        <div class="form-group">
          <label>目标用户 <span class="required">*</span></label>
          <input 
            v-model="form.targetUser"
            placeholder="谁会使用这个产品？"
          />
        </div>
        
        <div class="form-group">
          <label>已知竞品（选填）</label>
          <input 
            v-model="competitorsInput"
            placeholder="用逗号分隔多个竞品"
          />
        </div>
        
        <button 
          class="btn-primary"
          @click="submitForm"
          :disabled="!isFormValid || loading"
        >
          {{ loading ? '提取中...' : '提取关键词' }}
        </button>
      </div>
      
      <div v-if="showConfirm" class="confirm-section">
        <h2>确认信息</h2>
        
        <div class="confirm-content">
          <div class="confirm-item">
            <label>痛点</label>
            <p>{{ confirmData.problem }}</p>
          </div>
          <div class="confirm-item">
            <label>解决方案</label>
            <p>{{ confirmData.solution }}</p>
          </div>
          <div class="confirm-item">
            <label>目标用户</label>
            <p>{{ confirmData.targetUser }}</p>
          </div>
        </div>
        
        <div class="keywords-section">
          <label>搜索关键词</label>
          <div class="keywords-list">
            <span 
              v-for="(kw, idx) in keywords" 
              :key="idx"
              class="keyword-tag"
            >
              {{ kw }}
              <button @click="removeKeyword(idx)">×</button>
            </span>
          </div>
          <div class="keyword-input">
            <input 
              v-model="newKeyword"
              placeholder="添加关键词"
              @keyup.enter="addKeyword"
            />
            <button @click="addKeyword">添加</button>
          </div>
        </div>
        
        <button 
          class="btn-start"
          @click="startValidation"
        >
          开始验证
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const mode = ref('idea')
const rawIdea = ref('')
const form = ref({
  problem: '',
  solution: '',
  targetUser: ''
})
const competitorsInput = ref('')
const showConfirm = ref(false)
const confirmData = ref({})
const keywords = ref([])
const newKeyword = ref('')
const loading = ref(false)

const isFormValid = computed(() => {
  return form.value.problem.trim() && 
         form.value.solution.trim() && 
         form.value.targetUser.trim()
})

function switchMode(newMode) {
  mode.value = newMode
  showConfirm.value = false
  confirmData.value = {}
  keywords.value = []
}

async function submitIdea() {
  loading.value = true
  try {
    const res = await fetch('/api/extract/idea', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_idea: rawIdea.value })
    })
    const data = await res.json()
    
    confirmData.value = {
      problem: data.problem,
      solution: data.solution,
      targetUser: data.target_user
    }
    keywords.value = data.keywords || []
    showConfirm.value = true
  } catch (e) {
    alert('提取失败：' + e.message)
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  loading.value = true
  try {
    const res = await fetch('/api/extract/keywords', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        problem: form.value.problem,
        solution: form.value.solution,
        target_user: form.value.targetUser
      })
    })
    const data = await res.json()
    
    confirmData.value = {
      problem: form.value.problem,
      solution: form.value.solution,
      targetUser: form.value.targetUser
    }
    keywords.value = data.keywords || []
    showConfirm.value = true
  } catch (e) {
    alert('提取失败：' + e.message)
  } finally {
    loading.value = false
  }
}

function removeKeyword(idx) {
  keywords.value.splice(idx, 1)
}

function addKeyword() {
  if (newKeyword.value.trim() && !keywords.value.includes(newKeyword.value.trim())) {
    keywords.value.push(newKeyword.value.trim())
    newKeyword.value = ''
  }
}

async function startValidation() {
  try {
    const res = await fetch('/api/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        problem: confirmData.value.problem,
        solution: confirmData.value.solution,
        target_user: confirmData.value.targetUser,
        keywords: keywords.value
      })
    })
    const data = await res.json()
    router.push(`/validating/${data.task_id}`)
  } catch (e) {
    alert('提交失败：' + e.message)
  }
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: #F5F5F7;
  padding: 40px 20px;
}

.container {
  max-width: 800px;
  margin: 0 auto;
}

.title {
  font-size: 32px;
  font-weight: 600;
  text-align: center;
  margin-bottom: 8px;
}

.subtitle {
  text-align: center;
  color: #86868B;
  margin-bottom: 40px;
}

.entry-cards {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.card {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.card:hover {
  transform: scale(1.02);
}

.card.active {
  border-color: #007AFF;
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.15);
}

.card-icon {
  font-size: 40px;
  margin-bottom: 10px;
}

.card h3 {
  font-size: 18px;
  margin-bottom: 8px;
}

.card p {
  color: #86868B;
  font-size: 14px;
}

.idea-input textarea,
.form-input textarea,
.form-input input {
  width: 100%;
  padding: 12px;
  border: 1px solid #D2D2D7;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.2s;
}

.idea-input textarea:focus,
.form-input textarea:focus,
.form-input input:focus {
  outline: none;
  border-color: #007AFF;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.required {
  color: #FF3B30;
}

.btn-primary,
.btn-start {
  width: 100%;
  padding: 14px;
  background: #007AFF;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled),
.btn-start:hover {
  background: #0051D5;
  transform: scale(0.98);
}

.btn-primary:disabled {
  background: #D2D2D7;
  cursor: not-allowed;
}

.btn-start {
  background: #34C759;
  margin-top: 30px;
}

.btn-start:hover {
  background: #248A3D;
}

.confirm-section {
  background: white;
  border-radius: 12px;
  padding: 30px;
  margin-top: 30px;
}

.confirm-section h2 {
  margin-bottom: 20px;
}

.confirm-item {
  margin-bottom: 20px;
}

.confirm-item label {
  font-weight: 500;
  color: #86868B;
  font-size: 14px;
}

.confirm-item p {
  margin-top: 8px;
  font-size: 16px;
}

.keywords-section {
  margin-top: 30px;
}

.keywords-section label {
  font-weight: 500;
  display: block;
  margin-bottom: 12px;
}

.keywords-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.keyword-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #E5E5EA;
  border-radius: 20px;
  font-size: 14px;
}

.keyword-tag button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: #86868B;
}

.keyword-input {
  display: flex;
  gap: 8px;
}

.keyword-input input {
  flex: 1;
}

.keyword-input button {
  padding: 8px 16px;
  background: #007AFF;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
</style>
