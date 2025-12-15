import json

# 22個の性能指標の明確化
performance_indicators = [
    "Cost Efficiency",
    "Investment Requirements",
    "Price Competitiveness",
    "Carbon Footprint",
    "Environmental Compliance",
    "Resource Efficiency",
    "Accuracy",
    "Reliability",
    "Scalability",
    "Information Security",
    "Operational Safety",
    "Package Protection",
    "Coverage Performance",
    "Loading Performance",
    "Speed Performance",
    "Service Diversity",
    "Community Burden",
    "Inclusivity",
    "Worker Welfare",
    "Convenience",
    "Customer Support",
    "Transparency"
]

print("=" * 80)
print("設計案1: Urban Drone Delivery System")
print("=" * 80)
print("\nStep 1: 22個の性能指標を把握")
for i, perf in enumerate(performance_indicators, 1):
    print(f"{i:2d}. {perf}")

# Step 2: 各性能に対する特性（property）の設計
print("\nStep 2: 性能に影響を与える特性（property）の設計")

properties = [
    {"layer": 2, "type": "property", "label": "Battery Capacity"},
    {"layer": 2, "type": "property", "label": "Flight Speed"},
    {"layer": 2, "type": "property", "label": "Payload Capacity"},
    {"layer": 2, "type": "property", "label": "Navigation Precision"},
    {"layer": 2, "type": "property", "label": "Weather Resistance"},
    {"layer": 2, "type": "property", "label": "Noise Level"},
    {"layer": 2, "type": "property", "label": "Collision Avoidance System"},
    {"layer": 2, "type": "property", "label": "Data Encryption Level"},
    {"layer": 2, "type": "property", "label": "Automated Landing Accuracy"},
    {"layer": 2, "type": "property", "label": "Fleet Communication Protocol"},
    {"layer": 2, "type": "property", "label": "Energy Recovery System"},
    {"layer": 2, "type": "property", "label": "Package Securing Mechanism"}
]

# Step 3: Object と Environment の追加
print("\nStep 3: Object と Environment の設計")

objects = [
    {"layer": 4, "type": "object", "label": "Drone Aircraft"},
    {"layer": 4, "type": "object", "label": "Rooftop Landing Pads"},
    {"layer": 4, "type": "object", "label": "Charging Stations"},
    {"layer": 4, "type": "object", "label": "Central Control System"},
    {"layer": 4, "type": "object", "label": "Package Containers"},
    {"layer": 4, "type": "object", "label": "GPS Satellites"}
]

environments = [
    {"layer": 4, "type": "environment", "label": "Urban Airspace"},
    {"layer": 4, "type": "environment", "label": "Weather Patterns"},
    {"layer": 4, "type": "environment", "label": "Aviation Regulations"},
    {"layer": 4, "type": "environment", "label": "Building Density"},
    {"layer": 4, "type": "environment", "label": "Electromagnetic Interference"}
]

# Step 4: 変数（variable）の追加
print("\nStep 4: 変数（variable）の設計")

variables = [
    {"layer": 3, "type": "variable", "label": "Air Traffic Density"},
    {"layer": 3, "type": "variable", "label": "Fleet Utilization Rate"},
    {"layer": 3, "type": "variable", "label": "Route Optimization Algorithm"},
    {"layer": 3, "type": "variable", "label": "Maintenance Schedule"},
    {"layer": 3, "type": "variable", "label": "Charging Network Coverage"},
    {"layer": 3, "type": "variable", "label": "Customer Demand Patterns"},
    {"layer": 3, "type": "variable", "label": "Pilot Override Frequency"},
    {"layer": 3, "type": "variable", "label": "System Downtime"}
]

# Step 5: エッジの設計（性能への影響を中心に）
print("\nStep 5: エッジ（因果関係）の設計")

edges = [
    # Cost Efficiency への影響
    {"source": "Battery Capacity", "target": "Cost Efficiency", "weight": -1},
    {"source": "Fleet Utilization Rate", "target": "Cost Efficiency", "weight": -3},
    {"source": "Maintenance Schedule", "target": "Cost Efficiency", "weight": 1},
    
    # Investment Requirements への影響
    {"source": "Drone Aircraft", "target": "Investment Requirements", "weight": 3},
    {"source": "Rooftop Landing Pads", "target": "Investment Requirements", "weight": 3},
    {"source": "Central Control System", "target": "Investment Requirements", "weight": 3},
    
    # Price Competitiveness への影響
    {"source": "Fleet Utilization Rate", "target": "Price Competitiveness", "weight": -3},
    {"source": "Route Optimization Algorithm", "target": "Price Competitiveness", "weight": -1},
    
    # Carbon Footprint への影響
    {"source": "Battery Capacity", "target": "Carbon Footprint", "weight": -3},
    {"source": "Energy Recovery System", "target": "Carbon Footprint", "weight": -3},
    {"source": "Flight Speed", "target": "Carbon Footprint", "weight": 1},
    
    # Environmental Compliance への影響
    {"source": "Noise Level", "target": "Environmental Compliance", "weight": -3},
    {"source": "Energy Recovery System", "target": "Environmental Compliance", "weight": 3},
    {"source": "Aviation Regulations", "target": "Environmental Compliance", "weight": 1},
    
    # Resource Efficiency への影響
    {"source": "Battery Capacity", "target": "Resource Efficiency", "weight": 3},
    {"source": "Energy Recovery System", "target": "Resource Efficiency", "weight": 3},
    {"source": "Route Optimization Algorithm", "target": "Resource Efficiency", "weight": 3},
    
    # Accuracy への影響
    {"source": "Navigation Precision", "target": "Accuracy", "weight": 3},
    {"source": "Automated Landing Accuracy", "target": "Accuracy", "weight": 3},
    {"source": "GPS Satellites", "target": "Accuracy", "weight": 3},
    {"source": "Electromagnetic Interference", "target": "Accuracy", "weight": -1},
    
    # Reliability への影響
    {"source": "Weather Resistance", "target": "Reliability", "weight": 3},
    {"source": "Collision Avoidance System", "target": "Reliability", "weight": 3},
    {"source": "System Downtime", "target": "Reliability", "weight": -3},
    {"source": "Maintenance Schedule", "target": "Reliability", "weight": 3},
    
    # Scalability への影響
    {"source": "Urban Airspace", "target": "Scalability", "weight": -1},
    {"source": "Fleet Communication Protocol", "target": "Scalability", "weight": 3},
    {"source": "Charging Network Coverage", "target": "Scalability", "weight": 3},
    
    # Information Security への影響
    {"source": "Data Encryption Level", "target": "Information Security", "weight": 3},
    {"source": "Fleet Communication Protocol", "target": "Information Security", "weight": 1},
    {"source": "Central Control System", "target": "Information Security", "weight": 3},
    
    # Operational Safety への影響
    {"source": "Collision Avoidance System", "target": "Operational Safety", "weight": -3},
    {"source": "Weather Resistance", "target": "Operational Safety", "weight": -1},
    {"source": "Pilot Override Frequency", "target": "Operational Safety", "weight": 1},
    {"source": "Air Traffic Density", "target": "Operational Safety", "weight": 1},
    
    # Package Protection への影響
    {"source": "Package Securing Mechanism", "target": "Package Protection", "weight": 3},
    {"source": "Automated Landing Accuracy", "target": "Package Protection", "weight": 3},
    {"source": "Package Containers", "target": "Package Protection", "weight": 3},
    
    # Coverage Performance への影響
    {"source": "Battery Capacity", "target": "Coverage Performance", "weight": 3},
    {"source": "Charging Network Coverage", "target": "Coverage Performance", "weight": 3},
    {"source": "Building Density", "target": "Coverage Performance", "weight": -1},
    
    # Loading Performance への影響
    {"source": "Payload Capacity", "target": "Loading Performance", "weight": 3},
    {"source": "Package Containers", "target": "Loading Performance", "weight": 1},
    
    # Speed Performance への影響
    {"source": "Flight Speed", "target": "Speed Performance", "weight": 3},
    {"source": "Route Optimization Algorithm", "target": "Speed Performance", "weight": 3},
    {"source": "Air Traffic Density", "target": "Speed Performance", "weight": -1},
    
    # Service Diversity への影響
    {"source": "Payload Capacity", "target": "Service Diversity", "weight": 1},
    {"source": "Package Securing Mechanism", "target": "Service Diversity", "weight": 1},
    
    # Community Burden への影響
    {"source": "Noise Level", "target": "Community Burden", "weight": -3},
    {"source": "Rooftop Landing Pads", "target": "Community Burden", "weight": -1},
    
    # Inclusivity への影響
    {"source": "Building Density", "target": "Inclusivity", "weight": -1},
    {"source": "Rooftop Landing Pads", "target": "Inclusivity", "weight": -0.33},
    
    # Worker Welfare への影響
    {"source": "Central Control System", "target": "Worker Welfare", "weight": 3},
    {"source": "Pilot Override Frequency", "target": "Worker Welfare", "weight": -1},
    
    # Convenience への影響
    {"source": "Flight Speed", "target": "Convenience", "weight": 3},
    {"source": "Rooftop Landing Pads", "target": "Convenience", "weight": 3},
    {"source": "Customer Demand Patterns", "target": "Convenience", "weight": 1},
    
    # Customer Support への影響
    {"source": "Central Control System", "target": "Customer Support", "weight": 3},
    {"source": "System Downtime", "target": "Customer Support", "weight": -3},
    
    # Transparency への影響
    {"source": "GPS Satellites", "target": "Transparency", "weight": 3},
    {"source": "Central Control System", "target": "Transparency", "weight": 3},
    
    # Property間の関係
    {"source": "Battery Capacity", "target": "Flight Speed", "weight": 1},
    {"source": "Battery Capacity", "target": "Payload Capacity", "weight": -1},
    {"source": "Weather Patterns", "target": "Weather Resistance", "weight": -3},
    
    # Object -> Property の関係
    {"source": "Drone Aircraft", "target": "Battery Capacity", "weight": 3},
    {"source": "Drone Aircraft", "target": "Payload Capacity", "weight": 3},
    {"source": "Charging Stations", "target": "Charging Network Coverage", "weight": 3},
    
    # Environment -> Variable の関係
    {"source": "Urban Airspace", "target": "Air Traffic Density", "weight": 3},
    {"source": "Weather Patterns", "target": "Fleet Utilization Rate", "weight": -1},
    {"source": "Aviation Regulations", "target": "Pilot Override Frequency", "weight": 1}
]

# 全ノードの統合
all_nodes = properties + objects + environments + variables

# ネットワークの作成
network = {
    "design_case_name": "Urban Drone Delivery System",
    "nodes": all_nodes,
    "edges": edges
}

# 検証
print(f"\n作成されたネットワーク:")
print(f"- ノード数: {len(all_nodes)}")
print(f"  - Properties: {len(properties)}")
print(f"  - Objects: {len(objects)}")
print(f"  - Environments: {len(environments)}")
print(f"  - Variables: {len(variables)}")
print(f"- エッジ数: {len(edges)}")

# 性能指標へのエッジ数を確認
performance_edges = {}
for perf in performance_indicators:
    count = sum(1 for e in edges if perf in e['target'])
    performance_edges[perf] = count
    if count == 0:
        print(f"  ⚠️ {perf}: エッジなし")
    elif count < 2:
        print(f"  ⚠️ {perf}: {count}個のエッジ（少ない）")

print(f"\n性能指標への平均エッジ数: {sum(performance_edges.values()) / len(performance_indicators):.1f}")

# JSONファイルとして保存
with open('./outputs/network_01_urban_drone.json', 'w', encoding='utf-8') as f:
    json.dump(network, f, indent=2, ensure_ascii=False)

print(f"\n✅ ファイル保存: network_01_urban_drone.json")