// frontend/src/config/environment.ts

/**
 * 環境設定
 * 
 * VITE_APP_MODE環境変数により動作モードを切り替え
 * - local: ローカルモード（SQLite + ローカルファイル）
 * - web: Webモード（PostgreSQL + クラウド同期）
 */

export type EnvMode = 'local' | 'web';

export const ENV_MODE: EnvMode = (import.meta.env.VITE_APP_MODE as EnvMode) || 'local';

export const API_BASE_URL = ENV_MODE === 'web'
  ? import.meta.env.VITE_API_URL || 'https://your-server.com/api'
  : 'http://localhost:8000/api';

export const DATA_STORAGE = ENV_MODE === 'web' ? 'cloud' : 'local';

export const CONFIG = {
  mode: ENV_MODE,
  apiBaseUrl: API_BASE_URL,
  dataStorage: DATA_STORAGE,
  
  // 3D可視化設定
  mountain: {
    coneBaseRadius: 5.0,
    coneHeight: 10.0,
    pointSize: 0.15,
  },
  
  // ネットワークエディタ設定
  network: {
    layerHeight: 150,
    nodeSize: {
      performance: 80,
      property: 60,
      variable: 60,
      object: 70,
      condition: 60,
    },
    edgeColors: {
      type1: '#000000', // 黒
      type2: '#ff0000', // 赤
      type3: '#0000ff', // 青
      type4: '#00ff00', // 緑
    },
    nodeColors: {
      performance: '#FF6B6B',
      property: '#4ECDC4',
      variable: '#45B7D1',
      object: '#96CEB4',
      condition: '#FFEAA7',
    },
  },
};

// 開発用ログ
if (import.meta.env.DEV) {
  console.log('🔧 Environment Config:', CONFIG);
}
