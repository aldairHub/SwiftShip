files = [
    'api/orders.py',
    'api/charts.py',
    'charts/renderer.py',
    'filters/engine.py'
]

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = content.replace('FROM orders', 'FROM amazon_raw')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'Updated: {filepath}')

print('Done!')