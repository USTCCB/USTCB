import json
d = {}
for p in ['600','601','603']:
    for i in range(1000):
        c = f"{p}{i:03d}"
        d[c] = f"上交所{c}"
for p in ['000','001','002']:
    for i in range(1000):
        c = f"{p}{i:03d}"
        d[c] = f"深交所{c}"
# 添加真实名称
real = {'600000':'浦发银行','600519':'贵州茅台','601318':'中国平安','601398':'工商银行','000001':'平安银行','000002':'万科A','000333':'美的集团','000651':'格力电器','000858':'五粮液','002594':'比亚迪'}
d.update(real)
with open('stock_list.json','w',encoding='utf-8') as f:
    json.dump(d,f,ensure_ascii=False)
print(f"Done: {len(d)} stocks")
