import re

with open("/home/ubuntu/super-yandex-mcp/src/mcp_yandex_ad/hf_cdp.py", "r") as f:
    content = f.read()

# Fix funnel_report dimension
content = re.sub(
    r'goals_dim = ","\.join\(f"ym:s:goal\{id\}id" for id in goal_ids\)',
    'goals_dim = "ym:s:date"',
    content
)

# Fix comprehensive_audit funnel dimension
content = re.sub(
    r'goals_dim = ","\.join\(f"ym:s:goal\{id\}id" for id in goal_ids\)',
    'goals_dim = "ym:s:date"',
    content
)

# Fix revenue_report metrics
content = content.replace(
    'metrics = "ym:s:sumRevenue,ym:s:orderCount,ym:s:revenuePerOrder,ym:s:orderSumMargin"',
    'metrics = "ym:s:visits,ym:s:users"  # CDP counters do not support ecommerce metrics'
)

# Fix roi_report metrics
content = content.replace(
    'ym:s:sumRevenue,ym:s:orderSumCost,ym:s:sumProfit,ym:s:orderSumROI,ym:s:orderSumMargin,ym:s:orderSumMarginPercent',
    'ym:s:visits,ym:s:users'
)
content = content.replace(
    'metrics = (\n            "ym:s:sumRevenue,ym:s:orderSumCost,ym:s:sumProfit,"\n            "ym:s:orderSumROI,ym:s:orderSumMargin,ym:s:orderSumMarginPercent"\n        )',
    'metrics = "ym:s:visits,ym:s:users"'
)

# Fix crm_match_report metrics
content = content.replace(
    '"metrics": "ym:s:sumRevenue,ym:s:orderCount,ym:s:orderSumCost,ym:s:sumProfit"',
    '"metrics": "ym:s:visits,ym:s:users"'
)

# Fix comprehensive_audit LTV metrics
content = content.replace(
    '"metrics": "ym:s:visits,ym:s:users,ym:s:sumRevenue,ym:s:orderCount,ym:s:revenuePerUser"',
    '"metrics": "ym:s:visits,ym:s:users"'
)
content = content.replace(
    '"metrics": "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:sumRevenue"',
    '"metrics": "ym:s:visits,ym:s:users,ym:s:bounceRate"'
)


with open("/home/ubuntu/super-yandex-mcp/src/mcp_yandex_ad/hf_cdp.py", "w") as f:
    f.write(content)

