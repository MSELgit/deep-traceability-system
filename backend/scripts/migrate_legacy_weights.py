#!/usr/bin/env python3
"""
旧7段階モードの重みを新形式にマイグレーションするスクリプト

旧形式: {-3, -1, -1/3, 0, 1/3, 1, 3}
新形式: {-5, -3, -1, 0, 1, 3, 5}

Usage:
    python scripts/migrate_legacy_weights.py --dry-run  # プレビュー
    python scripts/migrate_legacy_weights.py            # 実行
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.weight_normalization import (
    migrate_legacy_7_level_weight,
    needs_7_level_migration,
    LEGACY_FRACTIONAL_TOLERANCE,
)


def migrate_network_weights(network: dict) -> tuple[dict, bool, list[str]]:
    """
    ネットワークのエッジ重みをマイグレーション

    Returns:
        (migrated_network, was_changed, changes_list)
    """
    edges = network.get('edges', [])
    changes = []
    was_changed = False

    new_edges = []
    for edge in edges:
        new_edge = edge.copy()
        weight = edge.get('weight')

        if weight is not None:
            # 旧形式の±1/3を検出
            is_old_third = (abs(weight - (1/3)) < LEGACY_FRACTIONAL_TOLERANCE or
                           abs(weight - (-1/3)) < LEGACY_FRACTIONAL_TOLERANCE)

            if is_old_third:
                new_weight = migrate_legacy_7_level_weight(weight)
                new_edge['weight'] = new_weight
                changes.append(f"  {edge.get('source', '?')} -> {edge.get('target', '?')}: {weight} → {new_weight}")
                was_changed = True

        new_edges.append(new_edge)

    new_network = network.copy()
    new_network['edges'] = new_edges
    return new_network, was_changed, changes


def migrate_database(db_path: str, dry_run: bool = True):
    """
    データベースの全design_casesをマイグレーション
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # design_casesを取得
    cursor.execute('''
        SELECT id, name, network_json, weight_mode
        FROM design_cases
        WHERE weight_mode = 'discrete_7' OR weight_mode = 'discrete'
    ''')

    rows = cursor.fetchall()
    total_cases = 0
    migrated_cases = 0

    print(f"\n{'=' * 60}")
    print(f"{'[DRY RUN] ' if dry_run else ''}Legacy Weight Migration")
    print(f"{'=' * 60}")
    print(f"Database: {db_path}")
    print(f"Total design cases with discrete_7/discrete mode: {len(rows)}\n")

    for row in rows:
        case_id = row['id']
        name = row['name']
        network_json = row['network_json']
        weight_mode = row['weight_mode']

        if not network_json:
            continue

        total_cases += 1
        network = json.loads(network_json)

        # マイグレーションが必要かチェック
        if not needs_7_level_migration(network.get('edges', [])):
            continue

        # マイグレーション実行
        new_network, was_changed, changes = migrate_network_weights(network)

        if was_changed:
            migrated_cases += 1
            print(f"\n[{migrated_cases}] {name} (mode={weight_mode})")
            for change in changes:
                print(change)

            if not dry_run:
                # データベースを更新
                cursor.execute('''
                    UPDATE design_cases
                    SET network_json = ?
                    WHERE id = ?
                ''', (json.dumps(new_network), case_id))

    if not dry_run:
        conn.commit()

    conn.close()

    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"  Total design cases checked: {total_cases}")
    print(f"  Cases with legacy weights: {migrated_cases}")
    if dry_run:
        print(f"\n  [DRY RUN] No changes were made. Run without --dry-run to apply.")
    else:
        print(f"\n  Successfully migrated {migrated_cases} design cases.")
    print(f"{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(description='Migrate legacy 7-level weights to new format')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying database')
    parser.add_argument('--db', type=str, default='data/local.db', help='Path to database file')
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Error: Database not found: {db_path}")
        sys.exit(1)

    migrate_database(str(db_path), dry_run=args.dry_run)


if __name__ == '__main__':
    main()
