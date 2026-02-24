"""检查仪表盘API返回的板块分布"""
import requests

print("检查仪表盘API返回的板块分布...")

response = requests.get("http://localhost:8000/api/v1/data/statistics")
print(f"状态码: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    stats = data.get('statistics', {})
    board_distribution = stats.get('board_distribution', {})
    
    print(f"\n板块分布:")
    for board, count in board_distribution.items():
        print(f"  {board}: {count}")
