<template>
  <header class="app-header">
    <div class="header-content">
      <h1 class="logo" @click="router.push('/')">
        <span class="logo-text">Deep Traceability System</span>
      </h1>
      <nav>
        <RouterLink to="/" class="nav-link">
          <span class="nav-text">Home</span>
        </RouterLink>
        <RouterLink to="/projects" class="nav-link">
          <span class="nav-text">Projects</span>
        </RouterLink>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'

const router = useRouter()
</script>

<style scoped lang="scss">
@import '../../style/color';

.app-header {
  background: $black;
  border-bottom: 1px solid transparentize($white, 0.95);
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5vh 5vw;
  max-width: 100vw;
}

.logo {
  font-size: clamp(1.2rem, 2vw, 1.5rem);
  font-weight: 800;
  cursor: pointer;
  margin: 0;
  transition: opacity 0.2s;
  display: flex;
  align-items: baseline;
  gap: 0.5vw;
}

.logo-text {
  background: linear-gradient(135deg, $main_1, $main_2);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.logo:hover {
  opacity: 0.8;
}

nav {
  display: flex;
  gap: 1vw;
}

.nav-link {
  position: relative;
  padding: 0.8vh 1.5vw;
  color: lighten($main_1, 10%);
  text-decoration: none;
  font-weight: 500;
  font-size: clamp(0.85rem, 1vw, 0.95rem);
  transition: all 0.3s ease;
  border-radius: 0.5vw;
}

.nav-link::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 2px;
  background: linear-gradient(135deg, $main_1, $main_2);
  transition: all 0.3s ease;
  transform: translateX(-50%);
}

.nav-link:hover {
  color: $white;
  background: transparentize($gray, 0.5);
}

.nav-link:hover::before {
  width: 80%;
}

.nav-link.router-link-active {
  color: $white;
  background: transparentize($main_1, 0.8);
}

.nav-link.router-link-active::before {
  width: 80%;
}

.nav-text {
  position: relative;
  z-index: 1;
}

@media (max-width: 768px) {
  .header-content {
    padding: 0vh 5vw;
  }
  
  .logo-accent {
    display: none;
  }
  
  nav {
    gap: 0.5vw;
  }
  
  .nav-link {
    padding: 0.8vh 1vw;
  }
}
</style>