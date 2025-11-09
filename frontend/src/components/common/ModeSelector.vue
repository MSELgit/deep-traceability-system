<template>
  <div class="mode-selector-overlay">
    <div class="mode-selector-card">
      <h2>実行モードを選択してください</h2>
      <p class="description">
        アプリケーションの動作モードを選択してください。<br />
        後から設定で変更することも可能です。
      </p>
      
      <div class="mode-options">
        <div class="mode-option" @click="selectMode('local')">
          <div class="mode-icon">💻</div>
          <h3>ローカルモード</h3>
          <p>
            データは端末内のみに保存されます。<br />
            インターネット接続不要で使用できます。
          </p>
          <button class="primary">ローカルモードで開始</button>
        </div>
        
        <div class="mode-option" @click="selectMode('web')">
          <div class="mode-icon">☁️</div>
          <h3>Webモード</h3>
          <p>
            クラウドにデータを保存します。<br />
            複数のデバイスから共同編集が可能です。
          </p>
          <button class="secondary">Webモードで開始</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const emit = defineEmits<{
  select: [mode: 'local' | 'web']
}>()

function selectMode(mode: 'local' | 'web') {
  emit('select', mode)
}
</script>

<style scoped>
.mode-selector-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.mode-selector-card {
  background: white;
  border-radius: 16px;
  padding: 40px;
  max-width: 900px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.mode-selector-card h2 {
  text-align: center;
  font-size: 28px;
  margin-bottom: 16px;
  color: #333;
}

.description {
  text-align: center;
  color: #666;
  margin-bottom: 40px;
  line-height: 1.6;
}

.mode-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

.mode-option {
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.mode-option:hover {
  border-color: #667eea;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
  transform: translateY(-4px);
}

.mode-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.mode-option h3 {
  font-size: 22px;
  margin-bottom: 16px;
  color: #333;
}

.mode-option p {
  color: #666;
  line-height: 1.6;
  margin-bottom: 24px;
  min-height: 60px;
}

.mode-option button {
  width: 100%;
  padding: 12px;
  font-size: 16px;
  font-weight: 600;
}
</style>
