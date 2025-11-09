<template>
  <header class="app-header">
    <div class="container">
      <div class="header-content">
        <h1 class="logo" @click="router.push('/')">
          Deep Traceability
        </h1>
        <nav>
          <RouterLink to="/">ホーム</RouterLink>
          <RouterLink to="/projects">プロジェクト</RouterLink>
        </nav>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'

const router = useRouter()
</script>

<style scoped>
.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
}

.logo {
  font-size: 24px;
  font-weight: 700;
  cursor: pointer;
  margin: 0;
  transition: opacity 0.2s;
}

.logo:hover {
  opacity: 0.8;
}

nav {
  display: flex;
  gap: 30px;
}

nav a {
  color: white;
  text-decoration: none;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

nav a:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

nav a.router-link-active {
  background-color: rgba(255, 255, 255, 0.2);
}
</style>
