<template>
  <div id="app">
    <ModeSelector v-if="!modeSelected" @select="onModeSelected" />
    <div v-else>
      <Header v-if="!isHomePage" />
      <main :class="{ 'no-padding': isHomePage }">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import Header from './components/common/Header.vue'
import ModeSelector from './components/common/ModeSelector.vue'

const route = useRoute()
const modeSelected = ref(false)

const isHomePage = computed(() => route.path === '/')

onMounted(() => {
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

<style scoped lang="scss">
@import './style/color';

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: $black;
}

main {
  flex: 1;
  padding: 0vh 5vw;
  background: $black;
  color: $white;
}

main.no-padding {
  padding: 0;
}
</style>
