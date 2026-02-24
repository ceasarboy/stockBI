"""检查baostock可用方法"""
import baostock as bs

print("=" * 60)
print("检查baostock可用方法")
print("=" * 60)

# 列出所有公开方法
public_methods = [m for m in dir(bs) if not m.startswith('_')]
print(f"\n公开方法 ({len(public_methods)} 个):")
for m in sorted(public_methods):
    print(f"  - {m}")

# 登录测试
print("\n登录测试...")
lg = bs.login()
print(f"登录结果: error_code={lg.error_code}, error_msg={lg.error_msg}")

# 检查是否有实时相关的方法
realtime_methods = [m for m in public_methods if 'real' in m.lower() or 'time' in m.lower() or 'current' in m.lower()]
print(f"\n实时相关方法: {realtime_methods}")

bs.logout()
