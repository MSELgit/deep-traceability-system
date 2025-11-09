# データベースマイグレーション手順: design_cases.color カラム追加

## 概要
`design_cases`テーブルに`color`カラムを追加するマイグレーション手順です。

---

## 既存のデータベースがある場合

### SQLiteの場合（開発環境）

データベースファイル: `backend/data/local.db`

#### 実行方法

```bash
cd backend
sqlite3 data/local.db
```

SQLiteのプロンプトで以下を実行:

```sql
-- colorカラムを追加
ALTER TABLE design_cases ADD COLUMN color TEXT DEFAULT '#3357FF';

-- 確認
PRAGMA table_info(design_cases);

-- データを確認
SELECT id, name, color FROM design_cases LIMIT 5;

-- 終了
.quit
```

#### ワンライナーで実行

```bash
cd backend/data
sqlite3 local.db "ALTER TABLE design_cases ADD COLUMN color TEXT DEFAULT '#3357FF';"
```

#### 確認

```bash
sqlite3 local.db "PRAGMA table_info(design_cases);"
```

---

## 新規データベースの場合

`database.py`の変更が既に反映されているので、`init_db()`を実行すれば自動的に`color`カラムが作成されます。

```python
# backend/app/models/database.py の init_db() を実行
from app.models.database import init_db
init_db()
```

---

## マイグレーションの確認

### Pythonスクリプトで確認

```python
# backend ディレクトリで実行
import sqlite3

conn = sqlite3.connect('data/local.db')
cursor = conn.cursor()

# テーブル構造を確認
cursor.execute("PRAGMA table_info(design_cases)")
columns = cursor.fetchall()

print("design_cases テーブルのカラム:")
for col in columns:
    print(f"  {col[1]} ({col[2]}) - デフォルト: {col[4]}")

conn.close()
```

### 期待される出力

```
design_cases テーブルのカラム:
  id (VARCHAR) - デフォルト: None
  project_id (VARCHAR) - デフォルト: None
  name (VARCHAR) - デフォルト: None
  description (TEXT) - デフォルト: None
  created_at (DATETIME) - デフォルト: None
  updated_at (DATETIME) - デフォルト: None
  performance_values_json (TEXT) - デフォルト: None
  network_json (TEXT) - デフォルト: None
  mountain_position_json (TEXT) - デフォルト: None
  utility_vector_json (TEXT) - デフォルト: None
  color (TEXT) - デフォルト: '#3357FF'  # ← これが追加される
```

---

## トラブルシューティング

### エラー: "duplicate column name: color"

すでに`color`カラムが存在しています。マイグレーションは不要です。

```bash
# 確認
sqlite3 data/local.db "PRAGMA table_info(design_cases);"
```

### エラー: "no such table: design_cases"

テーブルが存在しません。`init_db()`を実行してください。

```python
from app.models.database import init_db
init_db()
```

---

## 本番環境への適用

1. **バックアップを取る**
   ```bash
   cp data/local.db data/local.db.backup
   ```

2. **マイグレーションを実行**
   ```bash
   sqlite3 data/local.db "ALTER TABLE design_cases ADD COLUMN color TEXT DEFAULT '#3357FF';"
   ```

3. **確認**
   ```bash
   sqlite3 data/local.db "PRAGMA table_info(design_cases);"
   ```

4. **アプリケーションを再起動**
   ```bash
   # バックエンドサーバーを再起動
   uvicorn app.main:app --reload
   ```

---

## ロールバック方法

SQLiteではカラムの削除が直接できないため、テーブルを再作成する必要があります。

```sql
-- バックアップから復元
.backup data/local.db.backup

-- または、テーブルを再作成
BEGIN TRANSACTION;

-- 新しいテーブルを作成（colorカラムなし）
CREATE TABLE design_cases_new (
    id VARCHAR PRIMARY KEY,
    project_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    description TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    performance_values_json TEXT NOT NULL,
    network_json TEXT NOT NULL,
    mountain_position_json TEXT,
    utility_vector_json TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- データをコピー
INSERT INTO design_cases_new 
SELECT id, project_id, name, description, created_at, updated_at, 
       performance_values_json, network_json, mountain_position_json, utility_vector_json
FROM design_cases;

-- 古いテーブルを削除
DROP TABLE design_cases;

-- 新しいテーブルをリネーム
ALTER TABLE design_cases_new RENAME TO design_cases;

COMMIT;
```

---

## 関連ファイル

- モデル定義: `backend/app/models/database.py`
- スキーマ定義: `backend/app/schemas/project.py`
- データベースファイル: `backend/data/local.db`

---

## 実行済み

✅ 2025年10月23日: `local.db`に対してマイグレーション実行済み
