<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { api } from './api/client'
import WorldBookEditor from './components/WorldBookEditor.vue'
import CharacterCardEditor from './components/CharacterCardEditor.vue'
import StoryCharacters from './components/StoryCharacters.vue'

const games = ref([])
const game = ref(null)
const page = ref('library')
const busy = ref(false)
const error = ref('')
const action = ref('')
const retry = ref(null)
const latestScene = ref(null)
const fileInput = ref(null)
const importTarget = ref('create')
const savedBooks = ref([])
const savedCards = ref([])
const characters = ref([])
const selectedBook = ref('')
const selectedSettingsBook = ref('')
const assetTab = ref('worldbooks')
const editingBookId = ref(null)
const editingCardId = ref(null)
const libraryBook = ref({ name: '新世界书', entries: [newEntry()] })
const libraryCard = ref(blankCard())
const notice = ref('')
const storySettings = ref(null)
const form = ref({ title: '', persona: '', opening: '', style: '沉浸式小说，第二人称，细腻但不拖沓' })
const book = ref({ name: '我的世界', entries: [newEntry()] })
const lastTurn = computed(() => game.value?.turns.at(-1))
const currentPlayerCard = computed(() => game.value?.characters.find(character => character.enabled && character.role === 'player'))
const playerCard = computed(() => characters.value.find(character => character.enabled && character.role === 'player'))
const effectivePersona = computed(() => playerCard.value
  ? `你扮演${playerCard.value.card.name}。`
  : form.value.persona.trim())
const canStart = computed(() => form.value.title.trim() && effectivePersona.value
  && book.value.entries.some(entry => entry.enabled && entry.content.trim()))

function newEntry() {
  return { title: '世界与规则', content: '', keys: [], constant: true, enabled: true }
}

function blankCard() {
  return { name: '', description: '', personality: '', background: '', goal: '', scenario: '', first_mes: '', mes_example: '', worldbook: null }
}

function clone(value) {
  return JSON.parse(JSON.stringify(value))
}

async function loadAssets() {
  const [books, cards] = await Promise.all([api.listWorldbooks(), api.listCharacters()])
  savedBooks.value = books
  savedCards.value = cards
}

function showAssets() {
  page.value = 'assets'
  notice.value = ''
  return run(loadAssets)
}

function appendBook(target, imported) {
  const existing = target.entries.filter(entry => entry.content.trim())
  const added = clone(imported.entries).filter(entry => !existing.some(old => old.title === entry.title && old.content === entry.content))
  if (!existing.length) target.name = imported.name
  target.entries = [...existing, ...added]
}

function addSavedBook(target, id) {
  const saved = savedBooks.value.find(item => item.id === Number(id))
  if (saved) appendBook(target, saved.book)
}

function editLibraryBook(item = null) {
  editingBookId.value = item?.id ?? null
  libraryBook.value = item ? clone(item.book) : { name: '新世界书', entries: [newEntry()] }
  notice.value = ''
}

function editLibraryCard(item = null) {
  editingCardId.value = item?.id ?? null
  libraryCard.value = item ? clone(item.card) : blankCard()
  notice.value = ''
}

function saveLibraryBook() {
  const payload = clone(libraryBook.value)
  const id = editingBookId.value
  return run(async () => {
    const saved = await api.saveWorldbook(payload, id)
    editingBookId.value = saved.id
    await loadAssets()
    notice.value = '世界书已保存到设定库。已有故事不会自动同步。'
  })
}

function saveLibraryCard() {
  const payload = clone(libraryCard.value)
  const id = editingCardId.value
  return run(async () => {
    const saved = await api.saveCharacter(payload, id)
    editingCardId.value = saved.id
    await loadAssets()
    notice.value = '人设卡已保存到设定库，可在不同故事中重复使用。'
  })
}

function saveBookCopy(source) {
  const payload = clone(source)
  return run(async () => {
    await api.saveWorldbook(payload)
    await loadAssets()
    notice.value = '当前世界书已另存到设定库。'
  })
}

function saveCharacterCopy(card) {
  const payload = clone(card)
  return run(async () => {
    await api.saveCharacter(payload)
    await loadAssets()
    notice.value = '人物设定已另存到人设卡库。'
  })
}

function manageSettings() {
  return run(async () => {
    await loadAssets()
    storySettings.value = {
      worldbook: clone(game.value.worldbook), persona: game.value.persona, style: game.value.style,
      characters: clone(game.value.characters), expected_version: game.value.version,
      expected_settings_revision: game.value.settings_revision
    }
    notice.value = ''
    page.value = 'settings'
  })
}

function saveStorySettings() {
  const id = game.value.id
  const payload = clone(storySettings.value)
  const player = payload.characters.find(character => character.role === 'player' && character.enabled)
  if (player) payload.persona = `你扮演${player.card.name}。`
  return run(async () => {
    game.value = await api.updateGameSettings(id, payload)
    page.value = 'play'
    notice.value = '故事设定已保存，从下一幕生效。已有正文与记忆保留。'
  })
}

function pickImport(target) {
  importTarget.value = target
  fileInput.value.accept = target === 'asset-card' || target.includes('-card-') ? '.json,.txt,.md' : '.json,.txt,.md,.lorebook'
  fileInput.value.click()
}

async function run(task) {
  if (busy.value) return
  busy.value = true
  error.value = ''
  retry.value = null
  try {
    await task()
  } catch (err) {
    error.value = err.message || '操作失败，请稍后重试。'
    retry.value = task
  } finally {
    busy.value = false
  }
}

async function loadGames() {
  games.value = await api.listGames()
}

function showLibrary() {
  page.value = 'library'
  error.value = ''
  retry.value = null
  notice.value = ''
  return run(loadGames)
}

function showCreate() {
  page.value = 'create'
  error.value = ''
  retry.value = null
  notice.value = ''
  return run(loadAssets)
}

function example() {
  characters.value = []
  form.value = {
    title: '雾港来信', persona: '你叫林舟，是刚抵达雾港的旧物修复师，擅长观察机械细节。',
    opening: '雨夜，你来到姨母留下的钟表铺。柜台上有一封今天寄出、落款却是十年前失踪的父亲的信。',
    style: '悬疑与奇幻，第二人称，注重细节和线索，避免过早揭晓谜底'
  }
  book.value = { name: '雾港', entries: [
    { title: '雾港与规则', content: '雾港是一座被海雾包围的近代港城。旧物可能保留片段记忆，必须通过接触并修复才能读取。读取会消耗体力，不能随意获得完整真相。港城钟楼每晚十一点停摆一分钟。人物只能知道自己经历或被告知的事情。', keys: [], constant: true, enabled: true },
    { title: '钟表铺与姨母', content: '姨母沈岚是钟表铺主人，失踪三天。她行事谨慎，与码头邮差阿远相识。铺中有工作台、旧账本和上锁的地下室。玩家起初只有铺门钥匙、修复工具和少量旅费。', keys: [], constant: true, enabled: true },
    { title: '码头邮局', content: '码头邮局在每日清晨接收来自离岛的信件。邮差阿远怕水，却坚称自己曾在海雾中见过一座亮着灯的邮筒。', keys: ['码头', '邮差', '阿远', '邮局'], constant: false, enabled: true }
  ] }
}

function importFile(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const target = importTarget.value
  run(async () => {
    if (file.size > 1500000) throw new Error('文件过大，请导入 1.5 MB 以内的 UTF-8 文本或 JSON 世界书。')
    if (target === 'asset-card' || target.includes('-card-')) {
      const card = await api.importCharacter(await file.text(), file.name)
      if (target === 'asset-card') {
        libraryCard.value = card
        editingCardId.value = null
      } else {
        const role = target.endsWith('-player') ? 'player' : 'npc'
        const current = target.startsWith('settings-') ? storySettings.value.characters : characters.value
        const existing = role === 'player' ? current.filter(character => character.role !== 'player') : current
        if (existing.length >= 20) throw new Error('每个故事最多添加 20 张人设卡，请先移除部分角色。')
        const updated = [...existing, { card, role, enabled: true }]
        if (target.startsWith('settings-')) storySettings.value.characters = updated
        else characters.value = updated
      }
    } else {
      const imported = await api.importWorldbook(await file.text(), file.name)
      if (target === 'asset-book') {
        libraryBook.value = imported
        editingBookId.value = null
      } else if (target === 'settings') {
        appendBook(storySettings.value.worldbook, imported)
      } else {
        appendBook(book.value, imported)
        if (!form.value.title.trim()) form.value.title = imported.name
      }
    }
    notice.value = '文件已读入编辑区，请检查后保存。'
  })
  event.target.value = ''
}

function startGame() {
  const payload = { ...form.value, persona: effectivePersona.value, worldbook: clone(book.value), characters: clone(characters.value), request_id: crypto.randomUUID() }
  return run(async () => {
    const created = await api.createGame(payload)
    game.value = created
    action.value = ''
    page.value = 'play'
    notice.value = ''
    await scrollToLatest()
  })
}

function openGame(id) {
  return run(async () => {
    game.value = await api.getGame(id)
    action.value = ''
    page.value = 'play'
    notice.value = ''
    await scrollToLatest()
  })
}

function sendAction(text = action.value) {
  if (!text.trim() || !game.value) return
  const gameId = game.value.id
  const payload = { action: text.trim(), expected_version: game.value.version, expected_settings_revision: game.value.settings_revision, request_id: crypto.randomUUID() }
  return run(async () => {
    game.value = await api.actInGame(gameId, payload)
    action.value = ''
    notice.value = ''
    await scrollToLatest()
  })
}

async function scrollToLatest() {
  await nextTick()
  latestScene.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function dateLabel(value) {
  const date = new Date(value.endsWith('Z') || /[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`)
  return date.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => run(loadGames))
</script>

<template>
  <div class="game-app">
    <header class="site-header">
      <button class="brand" :disabled="busy" @click="showLibrary"><span class="brand-mark">N</span> NovelAgent <span class="brand-sub">互动叙事</span></button>
      <nav aria-label="主导航">
        <button class="nav-button" :class="{ selected: page === 'library' }" :disabled="busy" @click="showLibrary">我的故事</button>
        <button class="nav-button" :class="{ selected: page === 'assets' }" :disabled="busy" @click="showAssets">设定库</button>
        <button class="button small" :disabled="busy" @click="showCreate">＋ 新故事</button>
      </nav>
    </header>
    <input ref="fileInput" class="file-input" type="file" aria-label="导入设定文件" :disabled="busy" @change="importFile">
    <div v-if="notice" class="notice success-notice" role="status">{{ notice }}</div>

    <div v-if="error" class="notice error-notice" role="alert">
      <span>{{ error }}</span>
      <button v-if="retry" class="button small secondary" :disabled="busy" @click="run(retry)">重试</button>
    </div>
    <div v-if="busy" class="working" role="status"><span class="spinner"></span>{{ page === 'play' ? '故事正在继续，本幕完成后会自动保存…' : page === 'create' ? '正在准备你的世界，请稍候…' : '正在处理，请稍候…' }}</div>

    <main v-if="page === 'library'" class="library content-width">
      <section class="hero">
        <div class="hero-copy">
          <p class="kicker">YOUR WORLD. YOUR NEXT CHAPTER.</p>
          <h1>故事的下一步，<br>由你决定。</h1>
          <p class="muted hero-description">带上一个世界，成为其中的人。<br>在每次选择与行动中，写下只属于你的故事。</p>
          <button class="button" :disabled="busy" @click="showCreate">开启新的故事 <span>↗</span></button>
        </div>
        <div class="hero-art" aria-hidden="true"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div><div class="art-star">✦</div><div class="book-art"><span>每一个世界<br>都在等待<br><em>你的到来。</em></span><small>NOVELAGENT / 01</small></div></div>
      </section>
      <div class="section-heading"><div><p class="kicker">YOUR STORIES</p><h2>继续你的旅程</h2></div><span class="muted">{{ games.length }} 个本地存档</span></div>
      <div v-if="games.length" class="story-grid">
        <button v-for="(item, index) in games" :key="item.id" class="story-card" :disabled="busy" @click="openGame(item.id)">
          <div class="card-cover" :class="`cover-${index % 3}`"><span>WORLD / {{ String(index + 1).padStart(2, '0') }}</span><strong>{{ item.world_name }}</strong><i>✧</i></div>
          <div class="card-copy"><span class="card-meta">第 {{ item.version }} 幕 · {{ dateLabel(item.updated_at) }}</span><h3>{{ item.title }}</h3><p>{{ item.persona }}</p><span class="continue-link">继续故事 →</span></div>
        </button>
      </div>
      <section v-else-if="!busy" class="empty-state"><span>✧</span><h3>第一段旅程，从一个设定开始</h3><p class="muted">写下你的世界，或导入已有世界书。也可以先试试「雾港来信」示例。</p><button class="button secondary" @click="showCreate(); example()">体验示例世界 →</button></section>
      <p class="local-note">故事自动保存在当前后端的本地数据库中，稍后回来也能继续。</p>
    </main>

    <main v-else-if="page === 'assets'" class="asset-page content-width">
      <div class="page-heading"><p class="kicker">YOUR STORY MATERIALS</p><h1>设定，可以属于很多个故事。</h1><p class="muted">独立保存世界书与人设卡，开始新故事时选用，也能在旅途中继续添加。故事使用独立副本。</p></div>
      <div class="asset-tabs"><button class="nav-button" :class="{ selected: assetTab === 'worldbooks' }" :disabled="busy" @click="assetTab = 'worldbooks'; notice = ''">世界书 · {{ savedBooks.length }}</button><button class="nav-button" :class="{ selected: assetTab === 'characters' }" :disabled="busy" @click="assetTab = 'characters'; notice = ''">人设卡 · {{ savedCards.length }}</button></div>
      <div v-if="assetTab === 'worldbooks'" class="asset-layout">
        <aside class="surface asset-list"><button class="button secondary small" :disabled="busy" @click="editLibraryBook()">＋ 新建世界书</button><button v-for="item in savedBooks" :key="item.id" class="asset-list-item" :class="{ active: editingBookId === item.id }" :disabled="busy" @click="editLibraryBook(item)"><strong>{{ item.book.name }}</strong><span>{{ item.book.entries.length }} 条设定</span></button><p v-if="!savedBooks.length" class="field-help">还没有世界书，先写一本或导入文件。</p></aside>
        <form class="surface form-section" @submit.prevent="saveLibraryBook"><div class="section-heading"><h2>{{ editingBookId === null ? '新建世界书' : '编辑世界书' }}</h2><button class="button secondary small" type="button" :disabled="busy" @click="pickImport('asset-book')">↑ 导入文件</button></div><p class="field-help">支持文本、Markdown 和酒馆 JSON 世界书。导入内容先显示在编辑区，点击保存后才进入设定库。</p><WorldBookEditor :book="libraryBook" :busy="busy" /><button class="button" type="submit" :disabled="busy">保存世界书</button></form>
      </div>
      <div v-else class="asset-layout">
        <aside class="surface asset-list"><button class="button secondary small" :disabled="busy" @click="editLibraryCard()">＋ 新建人设卡</button><button v-for="item in savedCards" :key="item.id" class="asset-list-item" :class="{ active: editingCardId === item.id }" :disabled="busy" @click="editLibraryCard(item)"><strong>{{ item.card.name }}</strong><span>{{ item.card.personality || item.card.description || '人物设定' }}</span></button><p v-if="!savedCards.length" class="field-help">还没有人设卡。保存一次，以后可作为玩家或 NPC 复用。</p></aside>
        <form class="surface form-section" @submit.prevent="saveLibraryCard"><div class="section-heading"><h2>{{ editingCardId === null ? '新建人设卡' : '编辑人设卡' }}</h2><button class="button secondary small" type="button" :disabled="busy" @click="pickImport('asset-card')">↑ 导入人设卡</button></div><p class="field-help">先保存人物设定；用于故事时，可选择作为玩家本人或关键 NPC。支持酒馆 JSON 和文本人设，保留关联世界书；暂不支持 PNG 卡和脚本。</p><CharacterCardEditor :card="libraryCard" :busy="busy" /><button class="button" type="submit" :disabled="busy || !libraryCard.name.trim()">保存人设卡</button></form>
      </div>
    </main>

    <main v-else-if="page === 'settings' && storySettings" class="settings-page content-width">
      <div class="page-heading"><p class="kicker">STORY SETTINGS</p><h1>让世界，随着故事生长。</h1><p class="muted">正在编辑「{{ game.title }}」的独立设定。保存后从下一幕生效，已有正文、状态与记忆不会被改写。</p></div>
      <form class="settings-form" @submit.prevent="saveStorySettings">
        <section class="surface form-section"><div class="section-heading"><h2>世界书与补充设定</h2><button type="button" class="button secondary small" :disabled="busy" @click="pickImport('settings')">↑ 导入追加</button></div><div class="asset-picker"><select v-model="selectedSettingsBook" aria-label="选择追加世界书" :disabled="busy"><option value="">从世界书库选择…</option><option v-for="item in savedBooks" :key="item.id" :value="item.id">{{ item.book.name }}</option></select><button type="button" class="button secondary small" :disabled="busy || !selectedSettingsBook" @click="addSavedBook(storySettings.worldbook, selectedSettingsBook); selectedSettingsBook = ''">追加世界书</button></div><WorldBookEditor :book="storySettings.worldbook" :busy="busy" /><button type="button" class="text-button" :disabled="busy" @click="saveBookCopy(storySettings.worldbook)">将当前世界书另存到设定库</button></section>
        <section class="surface form-section"><h2>故事角色</h2><StoryCharacters v-model="storySettings.characters" v-model:persona="storySettings.persona" :library-cards="savedCards" :busy="busy" @save-card="saveCharacterCopy" @import-card="role => pickImport(`settings-card-${role}`)" /></section>
        <section class="surface form-section"><h2>叙事风格</h2><label>叙事风格<input v-model="storySettings.style" maxlength="1000" :disabled="busy"></label></section>
        <div class="settings-actions"><button class="button secondary" type="button" :disabled="busy" @click="page = 'play'; notice = ''">取消，返回故事</button><button class="button" type="submit" :disabled="busy">保存设定，继续故事 →</button></div>
      </form>
    </main>

    <main v-else-if="page === 'create'" class="create-page content-width">
      <div class="page-heading"><p class="kicker">CREATE A WORLD</p><h1>为故事，搭一座舞台。</h1><p class="muted">设定世界的边界，剩下的交给你的行动。</p></div>
      <form class="create-layout" @submit.prevent="startGame">
        <div class="create-main">
          <section class="surface form-section">
            <div class="section-heading"><h2><span class="section-number">01</span> 世界书</h2><div class="inline-actions"><button type="button" class="text-button" :disabled="busy" @click="example">填入示例</button><button type="button" class="button secondary small" :disabled="busy" @click="pickImport('create')">↑ 导入追加</button></div></div>
            <p class="field-help">支持 UTF-8 TXT / Markdown、酒馆世界书 JSON、角色卡内 character_book。导入会追加到当前设定；本版支持常驻、关键词和启用状态。</p>
            <div class="asset-picker"><select v-model="selectedBook" aria-label="选择世界书" :disabled="busy"><option value="">从世界书库选择…</option><option v-for="item in savedBooks" :key="item.id" :value="item.id">{{ item.book.name }}</option></select><button type="button" class="button secondary small" :disabled="busy || !selectedBook" @click="addSavedBook(book, selectedBook); selectedBook = ''">追加世界书</button></div>
            <WorldBookEditor :book="book" :busy="busy" />
            <button type="button" class="text-button" :disabled="busy" @click="saveBookCopy(book)">将当前世界书另存到设定库</button>
          </section>
          <section class="surface form-section">
            <h2><span class="section-number">02</span> 故事角色</h2>
            <StoryCharacters v-model="characters" v-model:persona="form.persona" :library-cards="savedCards" :busy="busy" @save-card="saveCharacterCopy" @import-card="role => pickImport(`create-card-${role}`)" />
          </section>
          <section class="surface form-section">
            <h2><span class="section-number">03</span> 故事与开场</h2>
            <label for="story-title">故事名称</label><input id="story-title" v-model="form.title" required maxlength="120" :disabled="busy" placeholder="给这段旅程起个名字">
            <label for="opening">故事从哪里开始？<span class="optional">可选</span></label><textarea id="opening" v-model="form.opening" rows="3" maxlength="3000" :disabled="busy" placeholder="一个场景、一场意外，或你想追寻的目标。留空由 AI 安排开场。" />
            <label for="style">叙事风格</label><input id="style" v-model="form.style" maxlength="1000" :disabled="busy" placeholder="例如：悬疑、温暖日常、史诗冒险">
          </section>
        </div>
        <aside class="surface start-panel"><span class="panel-symbol">✦</span><h2>准备好进入世界了吗？</h2><p class="muted">你的设定会成为故事的基础。开场后，可以选择推荐行动，也可以自由输入。</p><div class="start-detail"><span>叙事方式</span><strong>自由行动 · AI 主持</strong></div><div class="start-detail"><span>保存方式</span><strong>每幕自动保存</strong></div><button type="submit" class="button" :disabled="busy || !canStart">{{ busy ? '正在生成开场…' : '开始我的故事 →' }}</button><p class="field-help">首次生成可能需要一两分钟。请保持页面打开。</p></aside>
      </form>
    </main>

    <main v-else-if="page === 'play' && game" class="play-layout content-width">
      <aside class="play-sidebar">
        <section class="surface world-panel"><p class="kicker">CURRENT WORLD</p><h2>{{ game.title }}</h2><p class="muted">{{ game.world_name }} · 第 {{ game.version }} 幕</p><div class="divider"></div><h3>玩家本人</h3><p class="persona-copy">{{ currentPlayerCard ? currentPlayerCard.card.name : game.persona }}</p><div class="story-tools"><button class="button secondary small" :disabled="busy" @click="manageSettings">管理故事设定</button><button class="text-button" :disabled="busy" @click="openGame(game.id)">↻ 重新读取存档</button></div></section>
        <details v-if="game.characters.length" class="surface memory-panel"><summary>角色卡 · {{ game.characters.length }} 张</summary><div v-for="(character, index) in game.characters" :key="index"><h4>{{ character.card.name }} · {{ character.role === 'player' ? '玩家' : 'NPC' }}{{ character.enabled ? '' : ' · 已停用' }}</h4><p>{{ character.card.description }}</p></div></details>
        <section class="surface state-panel"><h3>此刻的你</h3><dl v-if="game.state.length"><div v-for="(fact, index) in game.state" :key="index"><dt>{{ fact.label }}</dt><dd>{{ fact.value }}</dd></div></dl><p v-else class="muted">故事刚刚开始。</p></section>
        <details class="surface memory-panel"><summary>旅程记忆</summary><p>{{ game.summary }}</p></details>
        <details class="surface memory-panel"><summary>世界设定 · {{ game.worldbook.entries.length }} 条</summary><div v-for="(entry, index) in game.worldbook.entries.filter(item => item.enabled)" :key="index"><h4>{{ entry.title }}</h4><p>{{ entry.content }}</p></div></details>
      </aside>
      <div class="story-column">
        <div class="reading-heading"><span class="kicker">THE STORY UNFOLDS</span><span class="save-indicator">● 已保存至第 {{ game.version }} 幕</span></div>
        <template v-for="turn in game.turns" :key="turn.turn_index">
          <div v-if="turn.action" class="player-action"><span>你的行动</span><p>{{ turn.action }}</p></div>
          <article class="scene surface" :class="{ 'current-scene': turn.turn_index === game.version }"><p class="scene-index">SCENE {{ String(turn.turn_index).padStart(2, '0') }} <span>✦</span></p><h2>{{ turn.title }}</h2><div class="scene-prose">{{ turn.content }}</div><div class="scene-end">· · ·</div></article>
        </template>
        <section ref="latestScene" class="action-panel surface">
          <p class="kicker">WHAT WILL YOU DO?</p><h3>接下来，你想怎么做？</h3>
          <div class="choices"><button v-for="(choice, index) in lastTurn?.choices || []" :key="index" :disabled="busy" @click="sendAction(choice)"><span>{{ String(index + 1).padStart(2, '0') }}</span>{{ choice }}<i>↗</i></button></div>
          <form @submit.prevent="sendAction()"><label for="action" class="field-help">或者，写下自己的行动</label><textarea id="action" v-model="action" rows="3" maxlength="3000" :disabled="busy" placeholder="例如：我收起信件，先检查柜台上的邮戳…" @keydown.ctrl.enter.prevent="sendAction()" /><div class="action-footer"><span class="field-help">Ctrl + Enter 发送 · 行动结果由剧情条件决定</span><button type="submit" class="button" :disabled="busy || !action.trim()">{{ busy ? '故事生成中…' : '行动 →' }}</button></div></form>
        </section>
      </div>
    </main>
    <footer class="site-footer">NovelAgent <span>一个世界，无数种可能。</span></footer>
  </div>
</template>
