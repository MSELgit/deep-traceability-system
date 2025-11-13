<template>
  <div class="home">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1 class="hero-title">Deep Traceability System</h1>
        <p class="hero-subtitle">
          Empowering complex system design through stakeholder-driven decision making
        </p>
        <div class="hero-actions">
          <button class="btn-primary" @click="router.push('/projects')">
            Start New Project
          </button>
          <button class="btn-secondary" @click="scrollToFeatures">
            Explore Features
          </button>
        </div>
      </div>
      <div class="hero-visual">
        <div class="floating-card card-1">
          <div class="card-label">Stakeholders</div>
        </div>
        <div class="floating-card card-2">
          <div class="card-label">Performance</div>
        </div>
        <div class="floating-card card-3">
          <div class="card-label">Design Cases</div>
        </div>
        <div class="center-sphere"></div>
      </div>
    </section>

    <!-- Features Grid -->
    <section class="features" ref="featuresSection">
      <h2 class="section-title">Key Features</h2>
      <div class="features-grid">
        <div class="feature-card">
          <h3>Stakeholder Analysis</h3>
          <p>Map needs to stakeholders with voting-based prioritization</p>
        </div>
        <div class="feature-card">
          <h3>Utility Design</h3>
          <p>Visual editor for continuous & discrete utility functions</p>
        </div>
        <div class="feature-card">
          <h3>3D Network</h3>
          <p>Interactive 4-layer structure visualization</p>
        </div>
        <div class="feature-card">
          <h3>Mountain View</h3>
          <p>Energy-based design evaluation on hemispheric surface</p>
        </div>
        <div class="feature-card">
          <h3>Trade-off Analysis</h3>
          <p>2-axis scatter plots for performance comparison</p>
        </div>
        <div class="feature-card">
          <h3>Data Management</h3>
          <p>Import/export with real-time sync capabilities</p>
        </div>
      </div>
    </section>

    <!-- Workflow Section -->
    <section class="workflow">
      <h2 class="section-title">How It Works</h2>
      <div class="workflow-container">
        <div class="workflow-step">
          <div class="step-number">1</div>
          <div class="step-content">
            <h4>Define Stakeholders</h4>
            <p>Identify & prioritize needs</p>
          </div>
        </div>
        <div class="workflow-connector"></div>
        <div class="workflow-step">
          <div class="step-number">2</div>
          <div class="step-content">
            <h4>Set Performance</h4>
            <p>Build hierarchical structure</p>
          </div>
        </div>
        <div class="workflow-connector"></div>
        <div class="workflow-step">
          <div class="step-number">3</div>
          <div class="step-content">
            <h4>Create Designs</h4>
            <p>Model 4-layer networks</p>
          </div>
        </div>
        <div class="workflow-connector"></div>
        <div class="workflow-step">
          <div class="step-number">4</div>
          <div class="step-content">
            <h4>Evaluate & Decide</h4>
            <p>Visualize & compare</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const featuresSection = ref<HTMLElement>()

const scrollToFeatures = () => {
  featuresSection.value?.scrollIntoView({ behavior: 'smooth' })
}
</script>

<style scoped lang="scss">
@import '../style/color';

.home {
  width: 100vw;
  height: 100vh;
  overflow-x: hidden;
  overflow-y: auto;
  background: $black;
  color: $white;
}

/* Hero Section */
.hero {
  height: 60vh;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 5vw;
  position: relative;
  overflow: hidden;
}

.hero-content {
  flex: 1;
  max-width: 45%;
  z-index: 2;
}

.hero-title {
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 800;
  margin-bottom: 1.5vh;
  background: linear-gradient(135deg, $main_1, $main_2);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.2;
}

.hero-subtitle {
  font-size: clamp(1rem, 2vw, 1.5rem);
  color: lighten($main_1, 10%);
  margin-bottom: 3vh;
  line-height: 1.5;
}

.hero-actions {
  display: flex;
  gap: 1.5vw;
  flex-wrap: wrap;
}

.btn-primary,
.btn-secondary {
  padding: 2vh 2.5vw;
  font-size: clamp(0.9rem, 1.2vw, 1.1rem);
  font-weight: 600;
  border: none;
  border-radius: 2vh;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5vw;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-primary {
  background: linear-gradient(135deg, $main_1, $main_2);
  color: $white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba($main_2, 0.4);
}

.btn-secondary {
  background: transparentize($gray, 0.7);
  color: $white;
  border: 1px solid transparentize($white, 0.8);
}

.btn-secondary:hover {
  background: transparentize($gray, 0.5);
  border-color: transparentize($white, 0.7);
}


/* Hero Visual */
.hero-visual {
  flex: 1;
  position: relative;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.center-sphere {
  width: 15vw;
  height: 15vw;
  background: radial-gradient(circle at 30% 30%, $main_1, $main_2);
  border-radius: 50%;
  box-shadow: 0 0 60px transparentize($main_1, 0.5);
  animation: pulse 4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.floating-card {
  position: absolute;
  background: transparentize($gray, 0.7);
  border: 1px solid transparentize($white, 0.9);
  border-radius: 1vw;
  padding: 1.5vh 2vw;
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-label {
  font-size: 1vw;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: $main_4;
}

.card-1 {
  top: 10%;
  left: 10%;
  animation: float1 6s ease-in-out infinite;
}

.card-2 {
  top: 60%;
  right: 20%;
  animation: float2 8s ease-in-out infinite;
}

.card-3 {
  bottom: 20%;
  left: 15%;
  animation: float3 7s ease-in-out infinite;
}

@keyframes float1 {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  33% { transform: translate(10px, -10px) rotate(2deg); }
  66% { transform: translate(-5px, 5px) rotate(-1deg); }
}

@keyframes float2 {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  50% { transform: translate(-15px, 10px) rotate(-2deg); }
}

@keyframes float3 {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  25% { transform: translate(5px, -5px) rotate(1deg); }
  75% { transform: translate(-10px, 5px) rotate(-2deg); }
}

/* Features Section */
.features {
  min-height: 50vh;
  padding: 5vh 5vw;
  background: $gray;
}

.section-title {
  text-align: center;
  font-size: clamp(2rem, 3vw, 3rem);
  margin-bottom: 5vh;
  color: $white;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 20vw), 1fr));
  gap: 2vw;
  max-width: 90vw;
  margin: 0 auto;
}

.feature-card {
  background: transparentize($white, 0.97);
  border: 1px solid transparentize($white, 0.95);
  border-radius: 1vw;
  padding: 4vh 2vw;
  text-align: center;
  transition: all 0.3s ease;
}

.feature-card:hover {
  background: transparentize($white, 0.95);
  border-color: transparentize($main_2, 0.7);
  transform: translateY(-0.5vh);
}


.feature-card h3 {
  font-size: clamp(1rem, 1.3vw, 1.25rem);
  margin-bottom: 1vh;
  color: $white;
}

.feature-card p {
  font-size: clamp(0.8rem, 1vw, 0.95rem);
  color: lighten($main_1, 10%);
  line-height: 1.5;
}

/* Workflow Section */
.workflow {
  padding: 5vh 5vw;
  background: $black;
}

.workflow-container {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1vw;
  max-width: 80vw;
  margin: 0 auto;
}

.workflow-step {
  flex: 1;
  text-align: center;
}

.step-number {
  width: 3vw;
  height: 3vw;
  background: linear-gradient(135deg, $main_1, $main_2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5vw;
  font-weight: 700;
  margin: 0 auto 1vh;
  color: $white;
}

.step-content h4 {
  font-size: clamp(0.9rem, 1.2vw, 1.15rem);
  margin-bottom: 0.5vh;
  color: $white;
}

.step-content p {
  font-size: clamp(0.75rem, 0.9vw, 0.85rem);
  color: lighten($main_1, 10%);
}

.workflow-connector {
  flex: 0.5;
  height: 2px;
  background: linear-gradient(to right, $main_1, $main_2);
  opacity: 0.3;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    padding: 3vh 5vw;
  }
  
  .hero-content {
    max-width: 100%;
    text-align: center;
  }
  
  .hero-actions {
    justify-content: center;
  }
  
  .hero-visual {
    display: none;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
    gap: 3vh;
  }
  
  .workflow-container {
    flex-direction: column;
    gap: 3vh;
  }
  
  .workflow-connector {
    width: 2px;
    height: 3vh;
    background: linear-gradient(to bottom, $main_1, $main_2);
  }
  
  .step-number {
    width: 50px;
    height: 50px;
    font-size: 1.5rem;
  }
}
</style>