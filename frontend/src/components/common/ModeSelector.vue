<template>
  <div class="mode-selector-overlay">
    <div class="mode-selector-card">
      <h1 class="selector-title">Select Your Mode</h1>
      <p class="selector-subtitle">
        Choose how you want to run the application
      </p>
      
      <div class="mode-options">
        <div class="mode-option local" @click="selectMode('local')">
          <div class="mode-header">
            <h3>Local Mode</h3>
            <span class="mode-badge">Offline</span>
          </div>
          <p class="mode-description">
            Data stored locally on your device.<br>
            No internet connection required.
          </p>
          <div class="mode-features">
            <div class="feature-item">Private & Secure</div>
            <div class="feature-item">Instant Access</div>
            <div class="feature-item">No Dependencies</div>
          </div>
          <button class="mode-button primary">
            Start Local Mode
          </button>
        </div>
        
        <div class="mode-option web" @click="selectMode('web')">
          <div class="mode-header">
            <h3>Web Mode</h3>
            <span class="mode-badge">Online</span>
          </div>
          <p class="mode-description">
            Cloud storage with real-time sync.<br>
            Collaborate across multiple devices.
          </p>
          <div class="mode-features">
            <div class="feature-item">Multi-device</div>
            <div class="feature-item">Collaboration</div>
            <div class="feature-item">Auto Backup</div>
          </div>
          <button class="mode-button secondary">
            Start Web Mode
          </button>
        </div>
      </div>
      
      <p class="selector-note">
        You can change this setting later in preferences
      </p>
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

<style scoped lang="scss">
@use 'sass:color';
@import '../../style/color';

.mode-selector-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: $black;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.mode-selector-card {
  background: $gray;
  border: 1px solid color.adjust($white, $alpha: -0.95);
  border-radius: 1.5vw;
  padding: 4vh 4vw;
  max-width: 70vw;
  width: 100%;
  max-height: 85vh;
  overflow: hidden;
}

.selector-title {
  text-align: center;
  font-size: clamp(2rem, 3vw, 3rem);
  font-weight: 800;
  margin-bottom: 1vh;
  background: linear-gradient(135deg, $main_1, $main_2);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.selector-subtitle {
  text-align: center;
  color: lighten($main_1, 10%);
  font-size: clamp(0.9rem, 1.2vw, 1.15rem);
  margin-bottom: 4vh;
}

.mode-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2vw;
  margin-bottom: 3vh;
}

.mode-option {
  background: color.adjust($white, $alpha: -0.98);
  border: 1px solid color.adjust($white, $alpha: -0.95);
  border-radius: 1vw;
  padding: 3vh 2.5vw;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.mode-option::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, transparent, transparent);
  transition: all 0.5s ease;
  opacity: 0;
}

.mode-option.local::before {
  background: radial-gradient(circle, color.adjust($main_1, $alpha: -0.9), transparent);
}

.mode-option.web::before {
  background: radial-gradient(circle, color.adjust($main_2, $alpha: -0.9), transparent);
}

.mode-option:hover {
  transform: translateY(-0.5vh);
  border-color: color.adjust($white, $alpha: -0.9);
}

.mode-option:hover::before {
  opacity: 1;
}

.mode-option.local:hover {
  border-color: color.adjust($main_1, $alpha: -0.7);
  box-shadow: 0 1vh 3vh color.adjust($main_1, $alpha: -0.8);
}

.mode-option.web:hover {
  border-color: color.adjust($main_2, $alpha: -0.7);
  box-shadow: 0 1vh 3vh color.adjust($main_2, $alpha: -0.8);
}

.mode-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5vh;
}

.mode-header h3 {
  font-size: clamp(1.2rem, 1.8vw, 1.75rem);
  font-weight: 700;
  color: $white;
  margin: 0;
}

.mode-badge {
  font-size: clamp(0.7rem, 0.8vw, 0.8rem);
  padding: 0.5vh 1vw;
  border-radius: 2vh;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.local .mode-badge {
  background: color.adjust($main_1, $alpha: -0.8);
  color: $main_1;
}

.web .mode-badge {
  background: color.adjust($main_2, $alpha: -0.8);
  color: $main_2;
}

.mode-description {
  color: lighten($main_1, 10%);
  line-height: 1.6;
  margin-bottom: 2vh;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  min-height: 6vh;
}

.mode-features {
  display: flex;
  flex-direction: column;
  gap: 0.8vh;
  margin-bottom: 3vh;
}

.feature-item {
  font-size: clamp(0.8rem, 0.9vw, 0.85rem);
  color: $main_1;
  padding-left: 1.5vw;
  position: relative;
}

.feature-item::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: $sub_4;
  font-weight: bold;
}

.mode-button {
  width: 100%;
  padding: 1.5vh 2vw;
  font-size: clamp(0.9rem, 1.1vw, 1rem);
  font-weight: 600;
  border: none;
  border-radius: 0.8vw;
  cursor: pointer;
  transition: all 0.3s ease;
}

.mode-button.primary {
  background: linear-gradient(135deg, $main_1, darken($main_1, 10%));
  color: $white;
}

.mode-button.primary:hover {
  background: linear-gradient(135deg, darken($main_1, 10%), darken($main_1, 20%));
  transform: translateY(-1px);
  box-shadow: 0 0.5vh 2vh color.adjust($main_1, $alpha: -0.7);
}

.mode-button.secondary {
  background: linear-gradient(135deg, $main_2, darken($main_2, 10%));
  color: $white;
}

.mode-button.secondary:hover {
  background: linear-gradient(135deg, darken($main_2, 10%), darken($main_2, 20%));
  transform: translateY(-1px);
  box-shadow: 0 0.5vh 2vh color.adjust($main_2, $alpha: -0.7);
}

.selector-note {
  text-align: center;
  color: $main_1;
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  margin-top: 2vh;
}

@media (max-width: 768px) {
  .mode-selector-card {
    padding: 3vh 5vw;
    max-width: 90vw;
  }
  
  .mode-options {
    grid-template-columns: 1fr;
    gap: 2vh;
  }
  
  .mode-option {
    padding: 2.5vh 4vw;
  }
}
</style>