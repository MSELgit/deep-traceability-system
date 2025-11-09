# Build stage
FROM node:18-alpine

WORKDIR /app

# package.jsonとpackage-lock.jsonをコピー
COPY package*.json ./

# 依存関係をインストール
RUN npm ci

# アプリケーションファイルをコピー
COPY . .

# ポート5173を公開
EXPOSE 5173

# Viteの開発サーバーを起動（ホスト0.0.0.0でリッスン）
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]