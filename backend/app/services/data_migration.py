# backend/app/services/data_migration.py
"""
データエクスポート/インポートのバージョン管理とマイグレーション

Phase 4: DB・スキーマ拡張で追加

バージョン履歴:
- 1.0.0: 初期構造
- 1.1.0: need.priority 追加
- 2.0.0: network.weight_mode, scc_analysis, paper_metrics, structural_analysis, kernel_type 追加
- 2.1.0: PAVE準拠: node.type 'property' → 'attribute' マイグレーション
- 2.2.0: 7段階重み形式変更: {-3,-1,-0.33,0,0.33,1,3} → {-5,-3,-1,0,1,3,5}
"""

import json
from typing import Dict, Any, List, Tuple
from datetime import datetime

# 現在のエクスポートバージョン
CURRENT_VERSION = "2.2.0"

# 旧7段階重みから新7段階重みへのマッピング
LEGACY_WEIGHT_MAP = {
    -3: -5,
    -1: -3,
    -0.33: -1,
    0: 0,
    0.33: 1,
    1: 3,
    3: 5
}

# 旧形式の判定用許容誤差（±0.33は浮動小数点で保存されている場合がある）
LEGACY_FRACTIONAL_TOLERANCE = 0.01


def get_export_metadata() -> Dict[str, Any]:
    """エクスポートメタデータを生成"""
    return {
        "version": CURRENT_VERSION,
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "format": "deep_traceability_system"
    }


def analyze_migrations(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    インポートデータのマイグレーション分析（適用はしない）

    Args:
        data: インポートされたJSONデータ

    Returns:
        {
            "needs_migration": bool,
            "source_version": str,
            "target_version": str,
            "migrations": [...],
            "user_choices": [
                {
                    "key": str,  # 選択のキー（migrate_import_dataに渡す）
                    "type": "single_select" | "number_input",
                    "label": str,
                    "description": str,
                    "options": [...],  # single_selectの場合
                    "default": any
                },
                ...
            ]
        }
    """
    migrations = []
    user_choices = []
    source_version = data.get("version", "1.0.0")

    # バージョンがない場合（古い形式）
    if "version" not in data:
        source_version = "1.0.0"

    current_version = source_version

    # 1.0.0 → 1.1.0: priority フィールド追加
    if _version_less_than(current_version, "1.1.0"):
        needs_without_priority = []
        for i, need in enumerate(data.get("needs", [])):
            if "priority" not in need:
                needs_without_priority.append({
                    "index": i,
                    "id": need.get("id", f"need_{i}"),
                    "name": need.get("name", f"Need {i}"),
                    "change": "priority: (missing) → 1.0"
                })

        if needs_without_priority:
            migrations.append({
                "type": "needs_priority",
                "description": "Add priority to needs",
                "affected_count": len(needs_without_priority),
                "details": needs_without_priority,
                "requires_user_choice": True
            })
            # 個別のNeedごとにpriority設定できるようにする
            user_choices.append({
                "key": "needs_priorities",
                "type": "needs_priority_table",
                "label": "Need Priorities",
                "description": "Set priority (0.0-1.0) for each need. Default is 1.0.",
                "needs": needs_without_priority,
                "default": {need["id"]: 1.0 for need in needs_without_priority}
            })
        current_version = "1.1.0"

    # 1.1.0 → 2.0.0: 構造分析関連フィールド追加
    if _version_less_than(current_version, "2.0.0"):
        cases_needing_fields = []
        for i, case in enumerate(data.get("design_cases", [])):
            missing_fields = []
            if "structural_analysis_json" not in case:
                missing_fields.append("structural_analysis_json")
            if "paper_metrics_json" not in case:
                missing_fields.append("paper_metrics_json")
            if "scc_analysis_json" not in case:
                missing_fields.append("scc_analysis_json")
            if "kernel_type" not in case:
                missing_fields.append("kernel_type → classic_wl")
            if "weight_mode" not in case:
                missing_fields.append("weight_mode → discrete_7")

            if missing_fields:
                cases_needing_fields.append({
                    "index": i,
                    "name": case.get("name", f"Case {i}"),
                    "missing_fields": missing_fields
                })

        if cases_needing_fields:
            migrations.append({
                "type": "design_case_fields",
                "description": "Add structural analysis fields to design cases",
                "affected_count": len(cases_needing_fields),
                "details": cases_needing_fields
            })
        current_version = "2.0.0"

    # 2.0.0 → 2.1.0: PAVE準拠 node.type 'property' → 'attribute'
    if _version_less_than(current_version, "2.1.0"):
        nodes_to_migrate = []
        for i, case in enumerate(data.get("design_cases", [])):
            if case.get("network_json"):
                try:
                    network = json.loads(case["network_json"])
                    for node in network.get("nodes", []):
                        if node.get("type") == "property":
                            nodes_to_migrate.append({
                                "case_index": i,
                                "case_name": case.get("name", f"Case {i}"),
                                "node_id": node.get("id"),
                                "node_label": node.get("label", node.get("id")),
                                "change": "type: property → attribute"
                            })
                except (json.JSONDecodeError, TypeError):
                    pass

        if nodes_to_migrate:
            migrations.append({
                "type": "node_type",
                "description": "Migrate node type from 'property' to 'attribute' (PAVE model)",
                "affected_count": len(nodes_to_migrate),
                "details": nodes_to_migrate
            })
        current_version = "2.1.0"

    # 2.1.0 → 2.2.0: 7段階重み形式変更
    if _version_less_than(current_version, "2.2.0"):
        weight_analysis = _analyze_weight_migrations(data)
        if weight_analysis["affected_count"] > 0 or weight_analysis.get("is_ambiguous"):
            migrations.append(weight_analysis)
            # 曖昧なケースではユーザー選択を追加
            if weight_analysis.get("is_ambiguous"):
                user_choices.append({
                    "key": "weight_format",
                    "type": "single_select",
                    "label": "Edge Weight Format",
                    "description": "Cannot auto-detect weight format. Please select the format used in this data.",
                    "options": [
                        {
                            "value": "legacy",
                            "label": "Legacy format (±3, ±1, 0)",
                            "description": "Weights will be converted: ±3→±5, ±1→±3"
                        },
                        {
                            "value": "new",
                            "label": "New format (±5, ±3, ±1, 0)",
                            "description": "No conversion needed"
                        }
                    ],
                    "default": "new"
                })
        current_version = "2.2.0"

    return {
        "needs_migration": len(migrations) > 0,
        "source_version": source_version,
        "target_version": CURRENT_VERSION,
        "migrations": migrations,
        "user_choices": user_choices
    }


def _analyze_weight_migrations(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    エッジ重みのマイグレーション分析

    旧7段階形式 {-3, -1, -0.33, 0, 0.33, 1, 3} を検出し、
    新7段階形式 {-5, -3, -1, 0, 1, 3, 5} への変換を分析

    Returns:
        is_ambiguous: ±0.33も±5もなく判定不能な場合True
    """
    edges_to_migrate = []
    weight_summary = {}  # weight value -> count
    has_legacy_fractional = False
    has_new_format = False
    has_ambiguous_weights = False  # ±3, ±1 のみ存在するケース
    ambiguous_weight_summary = {}  # 曖昧な場合の変換サマリー

    for i, case in enumerate(data.get("design_cases", [])):
        if case.get("network_json"):
            try:
                network = json.loads(case["network_json"])
                for edge in network.get("edges", []):
                    weight = edge.get("weight")
                    if weight is None:
                        continue

                    # ±0.33 の検出（旧形式の確定的な証拠）
                    if _is_legacy_fractional(weight):
                        has_legacy_fractional = True
                        new_weight = _map_legacy_weight(weight)
                        edges_to_migrate.append({
                            "case_index": i,
                            "case_name": case.get("name", f"Case {i}"),
                            "edge_id": edge.get("id"),
                            "old_weight": weight,
                            "new_weight": new_weight
                        })
                        # サマリーキーは統一フォーマットで生成
                        key = _format_weight_change(weight, new_weight)
                        weight_summary[key] = weight_summary.get(key, 0) + 1

                    # ±5 の検出（新形式の確定的な証拠）
                    elif abs(weight) == 5:
                        has_new_format = True

                    # ±3, ±1 の検出（曖昧：旧形式でも新形式でもあり得る）
                    elif _is_legacy_integer_weight(weight):
                        has_ambiguous_weights = True
                        # 曖昧なケース用のサマリーを構築
                        new_weight = LEGACY_WEIGHT_MAP.get(int(weight), weight)
                        key = _format_weight_change(weight, new_weight)
                        ambiguous_weight_summary[key] = ambiguous_weight_summary.get(key, 0) + 1

            except (json.JSONDecodeError, TypeError):
                pass

    # 曖昧なケースの判定:
    # - ±0.33がない（旧形式の確定証拠なし）
    # - ±5がない（新形式の確定証拠なし）
    # - ±3 or ±1 がある（どちらの形式でもあり得る値）
    is_ambiguous = (not has_legacy_fractional and
                    not has_new_format and
                    has_ambiguous_weights)

    # 旧形式が確定した場合、共通の値（±3, ±1）もマイグレーション対象
    if has_legacy_fractional and not has_new_format:
        for i, case in enumerate(data.get("design_cases", [])):
            if case.get("network_json"):
                try:
                    network = json.loads(case["network_json"])
                    for edge in network.get("edges", []):
                        weight = edge.get("weight")
                        if weight is None:
                            continue

                        # ±0.33 は既に処理済み
                        if _is_legacy_fractional(weight):
                            continue

                        # ±3, ±1 も旧形式としてマイグレーション
                        # 整数比較のため、floatも考慮（3.0 == 3）
                        if _is_legacy_integer_weight(weight):
                            new_weight = LEGACY_WEIGHT_MAP.get(int(weight), weight)
                            edges_to_migrate.append({
                                "case_index": i,
                                "case_name": case.get("name", f"Case {i}"),
                                "edge_id": edge.get("id"),
                                "old_weight": weight,
                                "new_weight": new_weight
                            })
                            key = _format_weight_change(weight, new_weight)
                            weight_summary[key] = weight_summary.get(key, 0) + 1

                except (json.JSONDecodeError, TypeError):
                    pass

    result = {
        "type": "edge_weights",
        "description": "Migrate edge weights from legacy 7-level to new 7-level format",
        "affected_count": len(edges_to_migrate),
        "has_legacy_format": has_legacy_fractional,
        "has_new_format": has_new_format,
        "is_ambiguous": is_ambiguous,
        "summary": weight_summary,
        "details": edges_to_migrate[:50]  # 最初の50件のみ詳細表示
    }

    # 曖昧なケースでは、旧形式として扱った場合の変換サマリーを追加
    if is_ambiguous:
        result["description"] = "Edge weight format is ambiguous - user selection required"
        result["ambiguous_summary"] = ambiguous_weight_summary
        result["requires_user_choice"] = True

    return result


def _is_legacy_integer_weight(weight: float) -> bool:
    """旧形式の整数重み（±3, ±1）かどうかを判定（3.0も3として扱う）"""
    int_weight = int(weight) if weight == int(weight) else None
    return int_weight in [-3, -1, 1, 3]


def _format_weight_change(old_weight: float, new_weight: float) -> str:
    """重み変換のサマリーキーを統一フォーマットで生成"""
    # 旧重みのフォーマット（±0.33は小数、それ以外は整数）
    if _is_legacy_fractional(old_weight):
        old_str = "0.33" if old_weight > 0 else "-0.33"
    else:
        old_str = str(int(old_weight))

    # 新重みは常に整数
    new_str = str(int(new_weight))

    return f"{old_str} → {new_str}"


def _is_legacy_fractional(weight: float) -> bool:
    """±0.33 (旧形式の1/3) かどうかを判定"""
    return (abs(weight - 0.33) < LEGACY_FRACTIONAL_TOLERANCE or
            abs(weight - (-0.33)) < LEGACY_FRACTIONAL_TOLERANCE or
            abs(weight - (1/3)) < LEGACY_FRACTIONAL_TOLERANCE or
            abs(weight - (-1/3)) < LEGACY_FRACTIONAL_TOLERANCE)


def _map_legacy_weight(weight: float) -> float:
    """旧形式の重みを新形式にマッピング"""
    # ±0.33 の処理
    if abs(weight - 0.33) < LEGACY_FRACTIONAL_TOLERANCE or abs(weight - (1/3)) < LEGACY_FRACTIONAL_TOLERANCE:
        return 1
    if abs(weight - (-0.33)) < LEGACY_FRACTIONAL_TOLERANCE or abs(weight - (-1/3)) < LEGACY_FRACTIONAL_TOLERANCE:
        return -1

    # その他の値
    return LEGACY_WEIGHT_MAP.get(weight, weight)


def migrate_import_data(data: Dict[str, Any], user_choices: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    インポートデータのバージョンマイグレーション

    古いバージョンのデータを最新バージョンに変換する。
    既存フィールドは維持し、新規フィールドはデフォルト値で追加。

    Args:
        data: インポートされたJSONデータ
        user_choices: ユーザーが選択した値（オプション）
            - default_priority: priorityのデフォルト値
            - weight_format: "legacy" | "new"

    Returns:
        マイグレーション済みのデータ
    """
    if user_choices is None:
        user_choices = {}

    version = data.get("version", "1.0.0")

    # バージョンがない場合（古い形式）
    if "version" not in data:
        version = "1.0.0"

    # 1.0.0 → 1.1.0: priority フィールド追加
    if _version_less_than(version, "1.1.0"):
        # 個別のNeed priorityを取得（なければデフォルト1.0）
        needs_priorities = user_choices.get("needs_priorities", {})
        for need in data.get("needs", []):
            if "priority" not in need:
                need_id = need.get("id", "")
                # ユーザーが設定した値があればそれを使用、なければ1.0
                need["priority"] = needs_priorities.get(need_id, 1.0)
        version = "1.1.0"

    # 1.1.0 → 2.0.0: 構造分析関連フィールド追加
    if _version_less_than(version, "2.0.0"):
        for case in data.get("design_cases", []):
            # 新規フィールドをデフォルト値で追加
            case.setdefault("structural_analysis_json", None)
            case.setdefault("paper_metrics_json", None)
            case.setdefault("scc_analysis_json", None)
            case.setdefault("kernel_type", "classic_wl")
            case.setdefault("weight_mode", "discrete_7")

            # network_jsonにweight_modeを追加
            if case.get("network_json"):
                try:
                    network = json.loads(case["network_json"])
                    network.setdefault("weight_mode", "discrete_7")
                    case["network_json"] = json.dumps(network, ensure_ascii=False)
                except (json.JSONDecodeError, TypeError):
                    pass

        version = "2.0.0"

    # 2.0.0 → 2.1.0: PAVE準拠 node.type 'property' → 'attribute'
    if _version_less_than(version, "2.1.0"):
        for case in data.get("design_cases", []):
            if case.get("network_json"):
                try:
                    network = json.loads(case["network_json"])
                    # Migrate node types
                    for node in network.get("nodes", []):
                        if node.get("type") == "property":
                            node["type"] = "attribute"
                    case["network_json"] = json.dumps(network, ensure_ascii=False)
                except (json.JSONDecodeError, TypeError):
                    pass
        version = "2.1.0"

    # 2.1.0 → 2.2.0: 7段階重み形式変更
    if _version_less_than(version, "2.2.0"):
        weight_format = user_choices.get("weight_format")  # "legacy" | "new" | None
        _apply_weight_migrations(data, weight_format)
        version = "2.2.0"

    # メタデータを更新
    data["version"] = version
    data["migrated_at"] = datetime.utcnow().isoformat() + "Z"

    return data


def _apply_weight_migrations(data: Dict[str, Any], user_weight_format: str = None) -> None:
    """
    エッジ重みのマイグレーションを適用

    Args:
        data: インポートデータ
        user_weight_format: ユーザーが選択した形式（"legacy" | "new" | None）
            Noneの場合は自動判定を使用
    """
    # まず旧形式かどうかを判定
    has_legacy_fractional = False
    has_new_format = False
    has_ambiguous_weights = False

    for case in data.get("design_cases", []):
        if case.get("network_json"):
            try:
                network = json.loads(case["network_json"])
                for edge in network.get("edges", []):
                    weight = edge.get("weight")
                    if weight is None:
                        continue
                    if _is_legacy_fractional(weight):
                        has_legacy_fractional = True
                    if abs(weight) == 5:
                        has_new_format = True
                    if _is_legacy_integer_weight(weight):
                        has_ambiguous_weights = True
            except (json.JSONDecodeError, TypeError):
                pass

    # 新形式が既に存在する場合はマイグレーションしない
    if has_new_format:
        return

    # マイグレーションを実行するかどうかの判定
    should_migrate = False

    if has_legacy_fractional:
        # ±0.33がある場合は確実に旧形式
        should_migrate = True
    elif user_weight_format == "legacy":
        # ユーザーが旧形式を選択した場合
        should_migrate = True
    elif user_weight_format == "new":
        # ユーザーが新形式を選択した場合はマイグレーションしない
        should_migrate = False
    elif has_ambiguous_weights and user_weight_format is None:
        # 曖昧なケースでユーザー選択がない場合はマイグレーションしない（安全側に倒す）
        should_migrate = False

    if not should_migrate:
        return

    # マイグレーション実行
    for case in data.get("design_cases", []):
        if case.get("network_json"):
            try:
                network = json.loads(case["network_json"])
                for edge in network.get("edges", []):
                    weight = edge.get("weight")
                    if weight is None:
                        continue

                    # ±0.33 の変換
                    if _is_legacy_fractional(weight):
                        edge["weight"] = _map_legacy_weight(weight)
                    # ±3, ±1 の変換（整数値として比較、3.0も3として扱う）
                    elif _is_legacy_integer_weight(weight):
                        edge["weight"] = LEGACY_WEIGHT_MAP.get(int(weight), weight)

                case["network_json"] = json.dumps(network, ensure_ascii=False)
            except (json.JSONDecodeError, TypeError):
                pass


def validate_import_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    インポートデータの検証

    Args:
        data: インポートされたJSONデータ

    Returns:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str],
            "version": str
        }
    """
    errors = []
    warnings = []

    # 必須フィールドのチェック
    if "project" not in data:
        errors.append("Missing required field: project")

    if "project" in data:
        project = data["project"]
        if "name" not in project:
            errors.append("Missing required field: project.name")

    # バージョンチェック
    version = data.get("version", "1.0.0")
    if _version_less_than(version, CURRENT_VERSION):
        warnings.append(f"Data version {version} will be migrated to {CURRENT_VERSION}")

    # 設計案の検証
    for i, case in enumerate(data.get("design_cases", [])):
        if "name" not in case:
            errors.append(f"design_cases[{i}]: Missing required field 'name'")
        if "performance_values_json" not in case:
            errors.append(f"design_cases[{i}]: Missing required field 'performance_values_json'")
        if "network_json" not in case:
            errors.append(f"design_cases[{i}]: Missing required field 'network_json'")
        else:
            # PAVE edge direction validation (warnings only - don't block import)
            try:
                network = json.loads(case["network_json"])
                pave_validation = validate_pave_edges(network)
                # PAVE violations are warnings, not errors, to allow importing legacy data
                for pave_error in pave_validation.get("errors", []):
                    warnings.append(f"design_cases[{i}] PAVE warning: {pave_error}")
                for pave_warning in pave_validation.get("warnings", []):
                    warnings.append(f"design_cases[{i}]: {pave_warning}")
            except (json.JSONDecodeError, TypeError):
                warnings.append(f"design_cases[{i}]: Could not parse network_json for PAVE validation")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "version": version
    }


def _version_less_than(v1: str, v2: str) -> bool:
    """バージョン比較（v1 < v2）"""
    def parse_version(v: str):
        parts = v.split(".")
        return tuple(int(p) for p in parts)

    return parse_version(v1) < parse_version(v2)


def validate_pave_edges(network: Dict[str, Any]) -> Dict[str, Any]:
    """
    PAVEモデルのエッジ方向ルールを検証

    Valid connections (source → target):
    - A → P: Attribute → Performance (layer 2 → 1)
    - V → A: Variable → Attribute (layer 3 → 2)
    - A → A: Attribute ↔ Attribute (layer 2 → 2, for loops)
    - V ↔ E: Variable ↔ Entity (layer 3 ↔ 4, bidirectional)
    - E ↔ E: Entity ↔ Entity (layer 4 ↔ 4)

    Invalid connections:
    - P → X: Performance → anything (layer 1 → X) - FORBIDDEN
    - V → P: Variable → Performance (layer 3 → 1) - FORBIDDEN
    - E → P: Entity → Performance (layer 4 → 1) - FORBIDDEN
    - E → A: Entity → Attribute (layer 4 → 2) - FORBIDDEN
    - V → V: Variable → Variable (layer 3 → 3) - FORBIDDEN
    - A → V: Attribute → Variable (layer 2 → 3) - FORBIDDEN

    Args:
        network: ネットワーク構造 {nodes: [...], edges: [...]}

    Returns:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str]
        }
    """
    errors = []
    warnings = []

    nodes = network.get("nodes", [])
    edges = network.get("edges", [])

    # Build node lookup
    node_map = {node.get("id"): node for node in nodes}

    for edge in edges:
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")

        source = node_map.get(source_id)
        target = node_map.get(target_id)

        if not source or not target:
            warnings.append(f"Edge references unknown node: {source_id} → {target_id}")
            continue

        from_layer = source.get("layer", 0)
        to_layer = target.get("layer", 0)
        from_label = source.get("label", source_id)
        to_label = target.get("label", target_id)

        # Performance (layer 1) cannot be a source
        if from_layer == 1:
            errors.append(
                f"Performance node '{from_label}' cannot be the source of an edge. "
                f"Edge '{from_label}' → '{to_label}' is invalid."
            )

        # Variable → Performance (layer 3 → 1) is FORBIDDEN
        elif from_layer == 3 and to_layer == 1:
            errors.append(
                f"Variable cannot connect directly to Performance. "
                f"Edge '{from_label}' → '{to_label}' should go through Attribute (V → A → P)."
            )

        # Entity → Performance (layer 4 → 1) is FORBIDDEN
        elif from_layer == 4 and to_layer == 1:
            errors.append(
                f"Entity cannot connect directly to Performance. "
                f"Edge '{from_label}' → '{to_label}' should go through V and A (E → V → A → P)."
            )

        # Entity → Attribute (layer 4 → 2) is FORBIDDEN
        elif from_layer == 4 and to_layer == 2:
            errors.append(
                f"Entity cannot connect directly to Attribute. "
                f"Edge '{from_label}' → '{to_label}' should go through Variable (E → V → A)."
            )

        # Variable → Variable (layer 3 → 3) is FORBIDDEN
        elif from_layer == 3 and to_layer == 3:
            errors.append(
                f"Variable cannot connect to another Variable. "
                f"Edge '{from_label}' → '{to_label}' is invalid. Variables are independent design parameters."
            )

        # Attribute → Variable (layer 2 → 3) is FORBIDDEN
        elif from_layer == 2 and to_layer == 3:
            errors.append(
                f"Attribute cannot connect to Variable. "
                f"Edge '{from_label}' → '{to_label}' is invalid. The causal flow is V → A → P."
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def add_export_fields_to_design_case(case_data: Dict[str, Any], db_case) -> Dict[str, Any]:
    """
    設計案のエクスポートデータに新規フィールドを追加

    Args:
        case_data: 基本エクスポートデータ
        db_case: DBモデルオブジェクト

    Returns:
        新規フィールドを含むエクスポートデータ
    """
    # Phase 4 新規フィールド
    case_data["structural_analysis_json"] = getattr(db_case, 'structural_analysis_json', None)
    case_data["paper_metrics_json"] = getattr(db_case, 'paper_metrics_json', None)
    case_data["scc_analysis_json"] = getattr(db_case, 'scc_analysis_json', None)
    case_data["kernel_type"] = getattr(db_case, 'kernel_type', 'classic_wl')
    case_data["weight_mode"] = getattr(db_case, 'weight_mode', 'discrete_7')

    return case_data
