<script setup>
defineProps({ book: { type: Object, required: true }, busy: Boolean })

function updateKeys(entry, value) {
  entry.keys = value.split(/[,，]/).map(key => key.trim()).filter(Boolean)
}
</script>

<template>
  <div class="book-editor">
    <label>世界书名称<input v-model="book.name" maxlength="120" required :disabled="busy" placeholder="例如：雾港、镜中王国"></label>
    <div v-for="(entry, index) in book.entries" :key="index" class="lore-entry">
      <div class="entry-heading"><strong>设定条目 {{ index + 1 }}</strong><div class="inline-actions"><label class="checkbox-label"><input v-model="entry.enabled" type="checkbox" :disabled="busy">启用</label><button v-if="book.entries.length > 1" class="text-button remove-button" type="button" :disabled="busy" @click="book.entries.splice(index, 1)">移除</button></div></div>
      <input v-model="entry.title" aria-label="条目名称" maxlength="200" :disabled="busy" placeholder="条目名称，例如：世界规则、主要人物">
      <textarea v-model="entry.content" :aria-label="`条目 ${index + 1} 正文`" rows="5" maxlength="24000" :disabled="busy" placeholder="描述时代、地点、人物、规则与禁忌。重要规则建议设为常驻。" />
      <div class="entry-options"><label class="checkbox-label"><input v-model="entry.constant" type="checkbox" :disabled="busy">常驻设定</label><input :value="entry.keys.join(', ')" aria-label="触发关键词" :disabled="busy || entry.constant" placeholder="触发关键词，用逗号分隔" @input="updateKeys(entry, $event.target.value)"></div>
      <p v-if="!entry.constant" class="field-help">匹配当前行动、近期剧情和记忆；无关键词的条目仍会常驻。</p>
    </div>
    <div class="entry-footer"><button class="text-button" type="button" :disabled="busy || book.entries.length >= 500" @click="book.entries.push({ title: '新设定', content: '', keys: [], constant: true, enabled: true })">＋ 添加设定条目</button><span class="muted">{{ book.entries.length }} 条 · {{ book.entries.reduce((sum, entry) => sum + entry.content.length, 0).toLocaleString() }} 字符</span></div>
  </div>
</template>
