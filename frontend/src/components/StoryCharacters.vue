<script setup>
import { computed, ref } from 'vue'
import CharacterCardEditor from './CharacterCardEditor.vue'

const props = defineProps({
  modelValue: { type: Array, required: true },
  persona: { type: String, default: '' },
  libraryCards: { type: Array, default: () => [] },
  busy: Boolean
})
const emit = defineEmits(['update:modelValue', 'update:persona', 'save-card', 'import-card'])
const playerPicker = ref(false)
const npcPicker = ref(false)
const selectedPlayer = ref('')
const selectedNpc = ref('')
const player = computed(() => props.modelValue.find(character => character.role === 'player' && character.enabled))
const npcs = computed(() => props.modelValue.map((character, index) => ({ character, index })).filter(item => item.character.role === 'npc'))
const canAddNpc = computed(() => props.modelValue.length < 20)
const canSetPlayer = computed(() => props.modelValue.filter(character => character.role !== 'player').length < 20)

function blankCard() {
  return { name: '', description: '', personality: '', background: '', goal: '', scenario: '', first_mes: '', mes_example: '', worldbook: null }
}

function attach(card, role) {
  const existing = role === 'player' ? props.modelValue.filter(character => character.role !== 'player') : props.modelValue
  if (existing.length >= 20) return
  emit('update:modelValue', [...existing, { card, role, enabled: true }])
  if (role === 'player') playerPicker.value = false
  else npcPicker.value = false
}

function selectCard(role) {
  const selection = role === 'player' ? selectedPlayer : selectedNpc
  const saved = props.libraryCards.find(item => item.id === Number(selection.value))
  if (!saved) return
  attach(JSON.parse(JSON.stringify(saved.card)), role)
  selection.value = ''
}

function removePlayer() {
  emit('update:modelValue', props.modelValue.filter(character => character.role !== 'player'))
  playerPicker.value = false
}
</script>

<template>
  <div class="story-characters">
    <section class="role-section player-section">
      <div class="role-heading"><div><h3>玩家本人</h3><p class="field-help">你在故事里是谁？选择一张人设卡，或直接写下身份。</p></div><span class="role-badge">你来扮演</span></div>
      <template v-if="player">
        <div class="selected-player"><strong>{{ player.card.name || '请填写玩家姓名' }}</strong><p>{{ player.card.description || '可展开下方编辑，补充身份、性格与经历。' }}</p></div>
        <details class="attached-character" :open="!player.card.name">
          <summary>编辑玩家人设</summary>
          <div class="character-toolbar"><button class="text-button" type="button" :disabled="busy || !player.card.name.trim()" @click="emit('save-card', player.card)">另存到人设卡库</button></div>
          <CharacterCardEditor :card="player.card" :busy="busy" />
        </details>
      </template>
      <label v-else class="player-description">玩家身份<textarea :value="persona" aria-label="玩家身份" rows="3" maxlength="3000" required :disabled="busy" placeholder="例如：沈照，24 岁的修理师，为寻找失踪的姐姐登上列车。" @input="emit('update:persona', $event.target.value)" /></label>
      <div class="role-source-actions"><button type="button" class="button secondary small" :disabled="busy || !canSetPlayer" @click="playerPicker = !playerPicker">{{ playerPicker ? '取消选卡' : (player ? '更换人设卡' : '选用人设卡') }}</button><button type="button" class="text-button" :disabled="busy || !canSetPlayer" @click="emit('import-card', 'player')">{{ player ? '导入并更换' : '导入玩家卡' }}</button><button v-if="!player" type="button" class="text-button" :disabled="busy || !canSetPlayer" @click="attach(blankCard(), 'player')">手写详细人设</button><button v-else type="button" class="text-button remove-button" :disabled="busy" @click="removePlayer">改用文字身份</button></div>
      <div v-if="playerPicker" class="role-library-picker"><label>选择玩家人设卡<select v-model="selectedPlayer" aria-label="选择玩家人设卡" :disabled="busy"><option value="">请选择…</option><option v-for="item in libraryCards" :key="item.id" :value="item.id">{{ item.card.name }}</option></select></label><button class="button secondary small" type="button" :disabled="busy || !selectedPlayer || !canSetPlayer" @click="selectCard('player')">{{ player ? '确认更换' : '使用这张卡' }}</button><p v-if="!libraryCards.length" class="field-help">人设卡库还是空的，可以导入文件或手写人设。</p></div>
      <button v-if="!player && persona.trim()" class="text-button save-persona-link" type="button" :disabled="busy" @click="emit('save-card', { ...blankCard(), name: '玩家人设', description: persona })">将这段身份另存为人设卡</button>
    </section>

    <section class="role-section npc-section">
      <div class="role-heading"><div><h3>关键 NPC <span class="optional">可选 · {{ npcs.length }} 位</span></h3><p class="field-help">同伴、对手或重要配角，由 AI 根据人设演绎。</p></div><button class="button secondary small" type="button" :disabled="busy || (!npcPicker && !canAddNpc)" @click="npcPicker = !npcPicker">{{ npcPicker ? '收起添加' : '＋ 添加角色' }}</button></div>
      <p v-if="!npcs.length && !npcPicker" class="role-empty">可以暂时留空，之后随剧情继续添加。</p>
      <div v-if="npcPicker" class="npc-add-panel"><div class="role-library-picker"><label>选择关键 NPC 人设卡<select v-model="selectedNpc" aria-label="选择关键 NPC 人设卡" :disabled="busy"><option value="">请选择…</option><option v-for="item in libraryCards" :key="item.id" :value="item.id">{{ item.card.name }}</option></select></label><button class="button secondary small" type="button" :disabled="busy || !selectedNpc || !canAddNpc" @click="selectCard('npc')">添加到故事</button></div><div class="role-source-actions"><button class="text-button" type="button" :disabled="busy || !canAddNpc" @click="emit('import-card', 'npc')">导入 NPC 卡</button><button class="text-button" type="button" :disabled="busy || !canAddNpc" @click="attach(blankCard(), 'npc')">手写 NPC 人设</button></div></div>
      <details v-for="{ character, index } in npcs" :key="index" class="attached-character npc-card" :open="!character.card.name">
        <summary>{{ character.card.name || '请填写角色姓名' }} <span class="muted">{{ character.enabled ? '' : ' · 已停用' }}</span></summary>
        <div class="character-toolbar"><label class="checkbox-label"><input v-model="character.enabled" type="checkbox" :disabled="busy">参与故事</label><button class="text-button" type="button" :disabled="busy || !character.card.name.trim()" @click="emit('save-card', character.card)">另存到人设卡库</button><button class="text-button remove-button" type="button" :disabled="busy" @click="emit('update:modelValue', modelValue.filter((_, position) => position !== index))">移除角色</button></div>
        <CharacterCardEditor :card="character.card" :busy="busy" />
      </details>
    </section>
  </div>
</template>
