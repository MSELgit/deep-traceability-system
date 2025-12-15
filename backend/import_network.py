import json
import sqlite3
import uuid
from typing import Dict, List, Any

def get_performance_mapping(conn: sqlite3.Connection, project_id: str) -> Dict[str, str]:
    """Get mapping of performance names to IDs for leaf performances."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name 
        FROM performances 
        WHERE project_id = ? AND is_leaf = 1
        ORDER BY name
    """, (project_id,))
    
    return {name: id for id, name in cursor.fetchall()}

def get_design_case_by_name(conn: sqlite3.Connection, project_id: str, name: str) -> str:
    """Get design case ID by name."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM design_cases 
        WHERE project_id = ? AND name = ?
    """, (project_id, name))
    
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"Design case '{name}' not found")
    
    return result[0]

def create_network_nodes(nodes_data: List[Dict], perf_mapping: Dict[str, str], canvas_width: int = 1200, canvas_height: int = 800) -> List[Dict]:
    """Create network nodes with auto-generated coordinates using NetworkEditor auto layout logic."""
    nodes = []
    
    # レイヤーごとの中央Y座標（キャンバス800を4分割）
    layer_center_y = [100, 300, 500, 700]  # レイヤー1-4の中央
    
    # ノード数が多い場合の2段組用のしきい値
    two_row_threshold = 12  # 12個以上で2段組
    layer_height = 120  # 2段の場合の行間隔
    
    # Auto-generate performance nodes (layer 1)
    perf_nodes = []
    perf_count = len(perf_mapping)
    y_center = layer_center_y[0]  # Layer 1
    
    if perf_count >= two_row_threshold:
        # 2段組
        nodes_per_row = (perf_count + 1) // 2  # Round up
        spacing = canvas_width / (nodes_per_row + 1)
        
        for i, (perf_name, perf_id) in enumerate(perf_mapping.items()):
            row = i // nodes_per_row
            col = i % nodes_per_row
            x = spacing * (col + 1)
            y = y_center + (layer_height/4 if row == 0 else -layer_height/4)
            
            perf_nodes.append({
                'id': f'perf-{perf_id}',
                'layer': 1,
                'type': 'performance',
                'label': perf_name,
                'x': x,
                'y': y,
                'performance_id': perf_id
            })
    else:
        # 1段組
        spacing = canvas_width / (perf_count + 1)
        for i, (perf_name, perf_id) in enumerate(perf_mapping.items()):
            x = spacing * (i + 1)
            y = y_center
            
            perf_nodes.append({
                'id': f'perf-{perf_id}',
                'layer': 1,
                'type': 'performance',
                'label': perf_name,
                'x': x,
                'y': y,
                'performance_id': perf_id
            })
    
    nodes.extend(perf_nodes)
    
    # Group nodes by layer for positioning
    layer_nodes = {}
    for node in nodes_data:
        layer = node['layer']
        if layer not in layer_nodes:
            layer_nodes[layer] = []
        layer_nodes[layer].append(node)
    
    # Position nodes by layer (layers 2-4)
    for layer in range(2, 5):
        if layer not in layer_nodes:
            continue
            
        layer_node_list = layer_nodes[layer]
        if not layer_node_list:
            continue
            
        y_center = layer_center_y[layer - 1]
        
        if layer == 4:
            # レイヤー4は特別な処理：モノを左半分、環境を右半分に配置
            object_nodes = [n for n in layer_node_list if n['type'] == 'object']
            env_nodes = [n for n in layer_node_list if n['type'] == 'environment']
            
            half_width = canvas_width / 2
            
            # モノを左半分に配置
            if object_nodes:
                if len(object_nodes) >= two_row_threshold:
                    nodes_per_row = (len(object_nodes) + 1) // 2
                    object_spacing = half_width / (nodes_per_row + 1)
                    for i, node in enumerate(object_nodes):
                        row = i // nodes_per_row
                        col = i % nodes_per_row
                        node_id = str(uuid.uuid4())
                        nodes.append({
                            'id': node_id,
                            'layer': layer,
                            'type': node['type'],
                            'label': node['label'],
                            'x': object_spacing * (col + 1),
                            'y': y_center + (layer_height/4 if row == 0 else -layer_height/4),
                            'performance_id': None
                        })
                else:
                    object_spacing = half_width / (len(object_nodes) + 1)
                    for i, node in enumerate(object_nodes):
                        node_id = str(uuid.uuid4())
                        nodes.append({
                            'id': node_id,
                            'layer': layer,
                            'type': node['type'],
                            'label': node['label'],
                            'x': object_spacing * (i + 1),
                            'y': y_center,
                            'performance_id': None
                        })
            
            # 環境を右半分に配置
            if env_nodes:
                if len(env_nodes) >= two_row_threshold:
                    nodes_per_row = (len(env_nodes) + 1) // 2
                    env_spacing = half_width / (nodes_per_row + 1)
                    for i, node in enumerate(env_nodes):
                        row = i // nodes_per_row
                        col = i % nodes_per_row
                        node_id = str(uuid.uuid4())
                        nodes.append({
                            'id': node_id,
                            'layer': layer,
                            'type': node['type'],
                            'label': node['label'],
                            'x': half_width + env_spacing * (col + 1),
                            'y': y_center + (layer_height/4 if row == 0 else -layer_height/4),
                            'performance_id': None
                        })
                else:
                    env_spacing = half_width / (len(env_nodes) + 1)
                    for i, node in enumerate(env_nodes):
                        node_id = str(uuid.uuid4())
                        nodes.append({
                            'id': node_id,
                            'layer': layer,
                            'type': node['type'],
                            'label': node['label'],
                            'x': half_width + env_spacing * (i + 1),
                            'y': y_center,
                            'performance_id': None
                        })
        else:
            # レイヤー2-3の処理
            node_count = len(layer_node_list)
            
            if node_count >= two_row_threshold:
                # 2段組
                nodes_per_row = (node_count + 1) // 2
                spacing = canvas_width / (nodes_per_row + 1)
                
                for i, node in enumerate(layer_node_list):
                    row = i // nodes_per_row
                    col = i % nodes_per_row
                    node_id = str(uuid.uuid4())
                    nodes.append({
                        'id': node_id,
                        'layer': layer,
                        'type': node['type'],
                        'label': node['label'],
                        'x': spacing * (col + 1),
                        'y': y_center + (layer_height/4 if row == 0 else -layer_height/4),
                        'performance_id': None
                    })
            else:
                # 1段組
                spacing = canvas_width / (node_count + 1)
                for i, node in enumerate(layer_node_list):
                    node_id = str(uuid.uuid4())
                    nodes.append({
                        'id': node_id,
                        'layer': layer,
                        'type': node['type'],
                        'label': node['label'],
                        'x': spacing * (i + 1),
                        'y': y_center,
                        'performance_id': None
                    })
    
    return nodes

def create_network_edges(edges_data: List[Dict], nodes: List[Dict], perf_mapping: Dict[str, str]) -> List[Dict]:
    """Create network edges with proper node ID mapping."""
    edges = []
    
    # Create label to node ID mapping
    label_to_id = {}
    for node in nodes:
        label_to_id[node['label']] = node['id']
    
    # Add performance name mappings
    for perf_name, perf_id in perf_mapping.items():
        label_to_id[perf_name] = f'perf-{perf_id}'
    
    for edge_data in edges_data:
        source_label = edge_data['source']
        target_label = edge_data['target']
        
        source_id = label_to_id.get(source_label)
        target_id = label_to_id.get(target_label)
        
        if not source_id:
            print(f"Warning: Source node '{source_label}' not found")
            continue
        if not target_id:
            print(f"Warning: Target node '{target_label}' not found")
            continue
        
        edge_id = str(uuid.uuid4())
        edges.append({
            'id': edge_id,
            'source_id': source_id,
            'target_id': target_id,
            'type': edge_data.get('type', 'type1'),  # Default to 'type1' if not specified
            'weight': edge_data.get('weight')
        })
    
    return edges

def update_design_case_network(conn: sqlite3.Connection, case_id: str, network_data: Dict):
    """Update design case with new network data."""
    cursor = conn.cursor()
    
    network_json = json.dumps(network_data, ensure_ascii=False)
    
    cursor.execute("""
        UPDATE design_cases 
        SET network_json = ?
        WHERE id = ?
    """, (network_json, case_id))
    
    if cursor.rowcount == 0:
        raise ValueError(f"Design case with ID '{case_id}' not found")

def import_single_network(json_file: str, project_id: str, db_path: str):
    """Import a single network from JSON file."""
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        # Read JSON data
        with open(json_file, 'r', encoding='utf-8') as f:
            network_data = json.load(f)
        
        print(f"Loading network for: {network_data['design_case_name']}")
        
        # Get performance mapping
        perf_mapping = get_performance_mapping(conn, project_id)
        
        # Get design case ID
        case_id = get_design_case_by_name(conn, project_id, network_data['design_case_name'])
        
        # Create nodes
        nodes = create_network_nodes(network_data['nodes'], perf_mapping)
        
        # Create edges
        edges = create_network_edges(network_data['edges'], nodes, perf_mapping)
        
        # Create network structure
        network_structure = {
            'nodes': nodes,
            'edges': edges
        }
        
        # Update design case
        update_design_case_network(conn, case_id, network_structure)
        conn.commit()
        
        print(f"✓ Successfully updated network for '{network_data['design_case_name']}' ({len(nodes)} nodes, {len(edges)} edges)")
        
        return True
        
    except Exception as e:
        print(f"Error importing {json_file}: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    """Import networks from JSON files."""
    project_id = '0cbd5e70-4f68-4da5-ba9d-7c5cdd21a561'
    db_path = '/Users/shimamon/deep-traceability-system/backend/data/local.db'
    outputs_dir = '/Users/shimamon/deep-traceability-system/backend/outputs'
    
    # Import all JSON files from 2 to 10
    success_count = 0
    error_count = 0
    
    for i in range(2, 11):
        json_file = f'{outputs_dir}/{i}.json'
        if import_single_network(json_file, project_id, db_path):
            success_count += 1
        else:
            error_count += 1
    
    print(f"\nBatch import completed: {success_count} successful, {error_count} failed")

if __name__ == "__main__":
    main()