<script setup>
import { computed, ref } from 'vue'
import { api } from './api/client'

const steps = [
  '输入想法',
  '确认设定',
  '确认章节事件',
  '生成章节',
  '确认章节',
  '查看记忆'
]

const step = ref(0)
const loading = ref(false)
const error = ref('')
const idea = ref('我想写一个未来城市里，失忆少女寻找自己身份的悬疑故事。')
const storyId = ref(null)
const settingsText = ref('')
const chapterEventText = ref('')
const chapterContent = ref('')
const assembledPrompt = ref('')
const memory = ref(null)
const generationTrace = ref([])
const confirmationTrace = ref([])
const userNote = ref('')
const rewriteNote = ref('')
const correction = ref({
  entity_id: '',
  entity_type: 'character',
  state_type: '',
  state_value: '',
  note: '用户手动修正'
})

const currentStepLabel = computed(() => steps[step.value])

function parseJson(text, label) {
  try {
    return JSON.parse(text)
  } catch {
    throw new Error(`${label} 不是合法 JSON，请检查格式。`)
  }
}

async function run(action) {
  loading.value = true
  error.value = ''
  try {
    await action()
  } catch (err) {
    error.value = err.message || String(err)
  } finally {
    loading.value = false
  }
}

function formatJson(value) {
  return JSON.stringify(value, null, 2)
}

function draftSettings() {
  return run(async () => {
    const draft = await api.draftSettings(idea.value)
    settingsText.value = formatJson(draft)
    step.value = 1
  })
}

function createStory() {
  return run(async () => {
    const settings = parseJson(settingsText.value, '故事设定')
    const created = await api.createStory(settings)
    storyId.value = created.story_id
    settingsText.value = formatJson(created.settings)
    const event = await api.draftChapterEvent(storyId.value, { user_note: userNote.value })
    chapterEventText.value = formatJson(event)
    step.value = 2
  })
}

function draftEvent() {
  return run(async () => {
    const event = await api.draftChapterEvent(storyId.value, { user_note: userNote.value })
    chapterEventText.value = formatJson(event)
  })
}

function draftChapter() {
  return run(async () => {
    const chapter_event = parseJson(chapterEventText.value, '章节事件')
    const draft = await api.draftChapter(storyId.value, {
      chapter_event,
      rewrite_note: rewriteNote.value
    })
    chapterContent.value = draft.content
    assembledPrompt.value = draft.assembled_prompt
    generationTrace.value = draft.workflow_trace || []
    step.value = 3
  })
}

function goConfirmChapter() {
  step.value = 4
}

function confirmChapter() {
  return run(async () => {
    const chapter_event = parseJson(chapterEventText.value, '章节事件')
    const result = await api.confirmChapter(storyId.value, {
      chapter_event,
      content: chapterContent.value
    })
    memory.value = await api.getMemory(storyId.value)
    confirmationTrace.value = result.workflow_trace || []
    step.value = 5
    assembledPrompt.value = formatJson(result.memory)
  })
}

function refreshMemory() {
  return run(async () => {
    memory.value = await api.getMemory(storyId.value)
  })
}

function submitCorrection() {
  return run(async () => {
    memory.value = await api.correctMemory(storyId.value, correction.value)
    correction.value = {
      entity_id: '',
      entity_type: 'character',
      state_type: '',
      state_value: '',
      note: '用户手动修正'
    }
  })
}

function nextChapter() {
  userNote.value = ''
  rewriteNote.value = ''
  chapterEventText.value = ''
  chapterContent.value = ''
  assembledPrompt.value = ''
  generationTrace.value = []
  confirmationTrace.value = []
  step.value = 2
  return draftEvent()
}
</script>

<template>
  <main class="shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">NovelAgent</p>
        <h1>多章节叙事生成</h1>
      </div>
      <div class="status">
        <span>当前阶段</span>
        <strong>{{ currentStepLabel }}</strong>
      </div>
    </header>

    <nav class="steps" aria-label="流程步骤">
      <button
        v-for="(item, index) in steps"
        :key="item"
        class="step"
        :class="{ active: index === step, done: index < step }"
        type="button"
      >
        <span>{{ index + 1 }}</span>
        {{ item }}
      </button>
    </nav>

    <p v-if="error" class="error">{{ error }}</p>

    <section v-if="step === 0" class="panel">
      <label for="idea">故事想法</label>
      <textarea id="idea" v-model="idea" rows="8" />
      <button :disabled="loading || !idea.trim()" @click="draftSettings">
        {{ loading ? '生成中...' : '生成设定卡' }}
      </button>
    </section>

    <section v-else-if="step === 1" class="panel">
      <label for="settings">故事设定 JSON</label>
      <textarea id="settings" v-model="settingsText" rows="18" spellcheck="false" />
      <button :disabled="loading" @click="createStory">
        {{ loading ? '保存中...' : '确认设定并生成第一章事件' }}
      </button>
    </section>

    <section v-else-if="step === 2" class="panel">
      <label for="note">本章补充要求</label>
      <input id="note" v-model="userNote" placeholder="可选，例如：节奏更悬疑" />
      <label for="event">章节事件 JSON</label>
      <textarea id="event" v-model="chapterEventText" rows="12" spellcheck="false" />
      <div class="actions">
        <button :disabled="loading" @click="draftEvent">重新生成事件</button>
        <button :disabled="loading || !chapterEventText.trim()" @click="draftChapter">
          {{ loading ? '生成中...' : '确认事件并生成章节' }}
        </button>
      </div>
    </section>

    <section v-else-if="step === 3" class="panel">
      <label for="rewrite">重写要求</label>
      <input id="rewrite" v-model="rewriteNote" placeholder="可选，例如：减少对白，增强环境压迫感" />
      <label for="chapter">章节正文</label>
      <textarea id="chapter" v-model="chapterContent" rows="20" />
      <details>
        <summary>检索上下文预览</summary>
        <pre>{{ assembledPrompt }}</pre>
      </details>
      <section v-if="generationTrace.length" class="workflow-trace">
        <h3>LangGraph 章节生成流程</h3>
        <ol>
          <li v-for="node in generationTrace" :key="node">{{ node }}</li>
        </ol>
      </section>
      <div class="actions">
        <button :disabled="loading" @click="draftChapter">重写</button>
        <button :disabled="loading || !chapterContent.trim()" @click="goConfirmChapter">使用这一版</button>
      </div>
    </section>

    <section v-else-if="step === 4" class="panel">
      <h2>确认章节</h2>
      <p>确认后会立即抽取状态、写入 SQLite，并把状态描述写入 Chroma。</p>
      <div class="chapter-preview">{{ chapterContent }}</div>
      <button :disabled="loading" @click="confirmChapter">
        {{ loading ? '写入记忆中...' : '确认章节并写入记忆' }}
      </button>
    </section>

    <section v-else class="panel">
      <div class="memory-header">
        <h2>当前记忆</h2>
        <button :disabled="loading" @click="refreshMemory">刷新</button>
      </div>
      <section v-if="confirmationTrace.length" class="workflow-trace">
        <h3>LangGraph 章节确认流程</h3>
        <ol>
          <li v-for="node in confirmationTrace" :key="node">{{ node }}</li>
        </ol>
      </section>
      <div v-if="memory" class="memory-grid">
        <section>
          <h3>最新状态</h3>
          <ul>
            <li v-for="item in memory.latest_states" :key="item.id">
              <strong>{{ item.entity_id }}.{{ item.state_type }}</strong>
              <span>{{ item.state_value }}</span>
            </li>
          </ul>
        </section>
        <section>
          <h3>章节摘要</h3>
          <ul>
            <li v-for="item in memory.chapter_summaries" :key="item.chapter_id">
              第 {{ item.chapter_id }} 章：{{ item.summary }}
            </li>
          </ul>
        </section>
        <section>
          <h3>滚动摘要</h3>
          <p>{{ memory.rolling_summary || '尚未触发滚动摘要。' }}</p>
        </section>
      </div>

      <form class="correction" @submit.prevent="submitCorrection">
        <h3>手动修正最新状态</h3>
        <input v-model="correction.entity_id" placeholder="entity_id，例如 char_linxia" required />
        <input v-model="correction.entity_type" placeholder="entity_type，例如 character" required />
        <input v-model="correction.state_type" placeholder="state_type，例如 location" required />
        <input v-model="correction.state_value" placeholder="新的状态值" required />
        <input v-model="correction.note" placeholder="修正原因" />
        <button :disabled="loading">保存修正</button>
      </form>

      <button class="primary" :disabled="loading" @click="nextChapter">进入下一章</button>
    </section>
  </main>
</template>
