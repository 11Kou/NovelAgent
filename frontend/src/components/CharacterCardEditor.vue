<script setup>
import WorldBookEditor from './WorldBookEditor.vue'
defineProps({ card: { type: Object, required: true }, busy: Boolean })
</script>

<template>
  <div class="character-editor">
    <label>角色姓名<input v-model="card.name" maxlength="120" required :disabled="busy" placeholder="给角色起个名字"></label>
    <label>身份与外貌<textarea v-model="card.description" rows="3" maxlength="12000" :disabled="busy" placeholder="角色的身份、外貌、能力与限制" /></label>
    <label>性格<input v-model="card.personality" maxlength="4000" :disabled="busy" placeholder="习惯、说话方式、面对冲突时的态度"></label>
    <label>背景<textarea v-model="card.background" rows="3" maxlength="6000" :disabled="busy" placeholder="人物经历与关系" /></label>
    <label>目标<input v-model="card.goal" maxlength="2000" :disabled="busy" placeholder="角色想要什么？"></label>
    <details class="card-extra"><summary>情境、开场白与对白示例</summary><label>人物情境<textarea v-model="card.scenario" rows="2" maxlength="4000" :disabled="busy" /></label><label>开场白<textarea v-model="card.first_mes" rows="2" maxlength="4000" :disabled="busy" /></label><label>对白示例<textarea v-model="card.mes_example" rows="3" maxlength="4000" :disabled="busy" /></label><p class="field-help">作为人物演绎参考；开场白不会在添加角色时直接插入已有正文。</p></details>
    <details v-if="card.worldbook" class="card-extra"><summary>角色关联世界书 · {{ card.worldbook.name }}</summary><WorldBookEditor :book="card.worldbook" :busy="busy" /></details>
  </div>
</template>
