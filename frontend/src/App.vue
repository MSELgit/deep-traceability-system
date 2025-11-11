<template>
  <div id="app">
    <!-- モード選択ダイアログ（初回のみ） -->
    <ModeSelector v-if="!modeSelected" @select="onModeSelected" />
    
    <!-- メインコンテンツ -->
    <div v-else>
      <Header />
      <main>
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterView } from 'vue-router'
import Header from './components/common/Header.vue'
import ModeSelector from './components/common/ModeSelector.vue'

const modeSelected = ref(false)

onMounted(() => {
  // ローカルストレージから選択済みモードを確認
  const savedMode = localStorage.getItem('appMode')
  if (savedMode) {
    modeSelected.value = true
  }
})

function onModeSelected(mode: 'local' | 'web') {
  localStorage.setItem('appMode', mode)
  modeSelected.value = true
}
</script>

<style scoped>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
  padding: 20px;
}
</style>
