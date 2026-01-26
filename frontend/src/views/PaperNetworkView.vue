<template>
  <div class="paper-network-view">
    <div class="header">
      <h1>論文用ネットワーク図 - No.1 カイト×横移動×輸送船</h1>
      <p>抽出されたノードとエッジのみを表示</p>
    </div>

    <div class="network-container" v-if="network">
      <NetworkViewer
        :network="network"
        :performances="[]"
      />
    </div>

    <div class="loading" v-else>
      <p>ネットワークデータを読み込み中...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import NetworkViewer from '../components/network/NetworkViewer.vue';
import type { NetworkStructure } from '../types/project';

const network = ref<NetworkStructure | null>(null);

const PROJECT_ID = '5a8b0f7b-5994-4eba-b0f6-2ee15340c07f';
const DESIGN_CASE_ID = 'e01c7509-e433-4a41-aae7-08091f124978';

onMounted(async () => {
  try {
    const response = await fetch(
      `http://localhost:8000/api/projects/${PROJECT_ID}/design-cases/${DESIGN_CASE_ID}/network/filtered`
    );

    if (response.ok) {
      const data = await response.json();
      network.value = data;
      console.log('Filtered network loaded:', data);
    } else {
      console.error('Failed to load filtered network:', response.status);
    }
  } catch (error) {
    console.error('Error loading filtered network:', error);
  }
});
</script>

<style scoped lang="scss">
@use 'sass:color';
@use '../style/color' as *;

.paper-network-view {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: $gray;
}

.header {
  padding: 1.5rem 2rem;
  background: linear-gradient(145deg, color.adjust($gray, $lightness: 10%), color.adjust($gray, $lightness: 6%));
  border-bottom: 1px solid color.adjust($white, $alpha: -0.95);
  color: $white;

  h1 {
    margin: 0 0 0.5rem 0;
    font-size: 1.5rem;
    font-weight: 600;
  }

  p {
    margin: 0;
    font-size: 0.9rem;
    color: color.adjust($white, $alpha: -0.3);
  }
}

.network-container {
  flex: 1;
  min-height: 0;
}

.loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $white;
  font-size: 1.2rem;
}
</style>
