<template>
  <div class="home">
    <div class="hero">
      <div class="container">
        <h1>Deep Traceability System</h1>
        <p class="subtitle">
          複雑システムの意思決定支援ツール
        </p>
        <div class="hero-buttons">
          <button class="primary large" @click="router.push('/projects')">
            プロジェクトを開始
          </button>
        </div>
      </div>
    </div>

    <div class="container">
      <section class="getting-started">
        <h2>使い方</h2>
        <ol class="steps">
          <li>
            <strong>プロジェクト作成</strong>
            <p>新しいシステム設計プロジェクトを作成します。</p>
          </li>
          <li>
            <strong>ステークホルダー登録</strong>
            <p>関係者とニーズを登録し、マトリクスで関係性を定義します。</p>
          </li>
          <li>
            <strong>性能定義</strong>
            <p>システムの性能を階層的に定義し、効用関数を設定します。</p>
          </li>
          <li>
            <strong>設計案作成</strong>
            <p>ネットワーク構造と性能値を入力して設計案を作成します。</p>
          </li>
          <li>
            <strong>山で可視化</strong>
            <p>3D空間で設計案を比較し、最適な案を探索します。</p>
          </li>
        </ol>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style scoped>
.hero {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 80px 0;
  text-align: center;
  margin-bottom: 60px;
}

.hero h1 {
  font-size: 48px;
  margin-bottom: 20px;
  font-weight: 700;
}

.subtitle {
  font-size: 24px;
  margin-bottom: 40px;
  opacity: 0.9;
}

.hero-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
}

button.large {
  padding: 16px 40px;
  font-size: 18px;
  font-weight: 600;
}

.getting-started {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 40px;
  margin-bottom: 60px;
}

.getting-started h2 {
  text-align: center;
  font-size: 36px;
  margin-bottom: 40px;
}

.steps {
  max-width: 800px;
  margin: 0 auto;
  counter-reset: step-counter;
  list-style: none;
}

.steps li {
  position: relative;
  padding-left: 60px;
  margin-bottom: 30px;
}

.steps li::before {
  counter-increment: step-counter;
  content: counter(step-counter);
  position: absolute;
  left: 0;
  top: 0;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
}

.steps li strong {
  display: block;
  font-size: 20px;
  margin-bottom: 8px;
  color: #333;
}

.steps li p {
  color: #666;
  line-height: 1.6;
}
</style>
