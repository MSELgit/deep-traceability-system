# 変更内容 (2025-12-21)

## 概要

Mountain Viewの**プロットサイズ（球体の大きさ）**がUIに表示される**Energy値と連動するように修正**しました。

### 修正前の問題
- プロットサイズは `utility_vector` の合計値で決定されていた
- UIに表示される「Energy」は `total_energy`（別の計算式）
- → **Energy が高いのにプロットが小さい**という不整合が発生

---

## 変更ファイル一覧

### バックエンド

#### 1. `backend/app/services/mountain_calculator.py`
- エネルギー計算の順序を変更（座標保存前に計算）
- `mountain_position_json` に `total_energy` を含めて保存

```python
# 575-581行目付近
case.mountain_position_json = json.dumps({
    'x': positions[i]['x'],
    'y': positions[i]['y'],
    'z': positions[i]['z'],
    'H': positions[i]['H'],
    'total_energy': energy_result['total_energy']  # 追加
})
```

#### 2. `backend/app/api/projects.py`
- `recalculate-mountains` エンドポイント（1720-1726行目付近）で `total_energy` を保存

```python
design_case.mountain_position_json = json.dumps({
    'x': pos['x'],
    'y': pos['y'],
    'z': pos['z'],
    'H': pos['H'],
    'total_energy': pos.get('energy', {}).get('total_energy', 0)  # 追加
})
```

#### 3. `backend/app/schemas/project.py`
- `MountainPosition` スキーマに `total_energy` フィールドを追加

```python
class MountainPosition(BaseModel):
    x: float
    y: float
    z: float
    H: float
    total_energy: Optional[float] = None  # 追加
```

### フロントエンド

#### 4. `frontend/src/components/mountain/MountainView.vue`
- プロットサイズ計算を `utility_vector` 合計 → `total_energy` に変更
- エネルギー差分が小さい場合（20%未満）はべき乗変換で差を強調

```typescript
// 486-504行目付近
const variationRatio = maxEnergy > 0 ? energyRange / maxEnergy : 0;
const enhancementPower = variationRatio < 0.2 ? 0.5 : 1.0;

// ...

const energy = designCase.mountain_position.total_energy || 0;
let normalizedEnergy = energyRange > 0 ? (energy - minEnergy) / energyRange : 0;
normalizedEnergy = Math.pow(normalizedEnergy, enhancementPower);
const sphereRadius = 0.35 + normalizedEnergy * 0.4;
```

#### 5. `frontend/src/types/project.ts`
- `MountainPosition` 型に `total_energy` を追加

```typescript
export interface MountainPosition {
    x: number;
    y: number;
    z: number;
    H: number;
    total_energy?: number;  // 追加
}
```

---

## データ更新方法

既存のデータには `total_energy` が含まれていないため、**再計算が必要**です。

### 手順
1. バックエンドサーバーを再起動（または `--reload` で自動反映を確認）
2. フロントエンドをリロード
3. Mountain View を開く
4. **「Recalculate Coordinates」ボタンをクリック**
5. 全設計案の `total_energy` が保存され、プロットサイズに反映される

---

## 動作確認

再計算後、以下を確認:
- UIの「Energy」値が高い設計案ほど、3D山のプロットが大きくなる
- エネルギー差分が小さくても、差が視覚的に分かりやすくなっている（べき乗変換により）

---

## 注意事項

- 再計算しないと `total_energy` が `null` のままで、全プロットが最小サイズになります
- 新規作成した設計案は自動で `total_energy` が設定されます
