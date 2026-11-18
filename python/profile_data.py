"""Profile the original Olist CSVs using Python's standard library only.

Run from any folder: python A:/olist-delivery-analytics/python/profile_data.py
Does not modify source data. Outputs aggregate diagnostics, never customer rows.
"""
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
OUT = ROOT / 'docs'
TABLES = {
    'orders': ('olist_orders_dataset.csv', ['order_id']),
    'customers': ('olist_customers_dataset.csv', ['customer_id']),
    'items': ('olist_order_items_dataset.csv', ['order_id', 'order_item_id']),
    'payments': ('olist_order_payments_dataset.csv', ['order_id', 'payment_sequential']),
    'reviews': ('olist_order_reviews_dataset.csv', None),
    'products': ('olist_products_dataset.csv', ['product_id']),
    'sellers': ('olist_sellers_dataset.csv', ['seller_id']),
    'geolocation': ('olist_geolocation_dataset.csv', None),
    'translation': ('product_category_name_translation.csv', ['product_category_name']),
}


def main():
    report = {'source': str(RAW), 'tables': {}, 'relationships': {}, 'notes': [
        'Historical Brazilian Olist data, 2016–2018; monetary values in BRL.',
        'Review IDs and geolocation ZIP prefixes are not assumed unique.',
        'Exact duplicate rows are reported, not automatically removed.',
        'Diagnostics are not analytical findings; investigate anomalies before publishing.'
    ]}
    data = {}
    for name, (filename, key) in TABLES.items():
        matches = list(RAW.rglob(filename))
        if len(matches) != 1:
            report['tables'][name] = {'error': f'Expected one {filename}; found {len(matches)}'}
            continue
        with matches[0].open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
            rows = list(reader)
        data[name] = rows
        signatures = Counter(tuple(row.get(c, '') for c in columns) for row in rows)
        entry = {
            'file': str(matches[0].relative_to(ROOT)), 'rows': len(rows),
            'columns': columns,
            'missing': {c: sum(not (r.get(c) or '').strip() for r in rows) for c in columns},
            'exact_duplicate_excess': sum(n - 1 for n in signatures.values()),
        }
        if key:
            if not set(key).issubset(columns):
                entry['key_error'] = 'Required key columns missing'
            else:
                counts = Counter(tuple(r[c] for c in key) for r in rows)
                entry['key'] = key
                entry['duplicate_key_excess'] = sum(n - 1 for n in counts.values())
        report['tables'][name] = entry

    relations = [
        ('orders', 'customer_id', 'customers', 'customer_id'),
        ('items', 'order_id', 'orders', 'order_id'),
        ('payments', 'order_id', 'orders', 'order_id'),
        ('reviews', 'order_id', 'orders', 'order_id'),
        ('items', 'product_id', 'products', 'product_id'),
        ('items', 'seller_id', 'sellers', 'seller_id'),
        ('products', 'product_category_name', 'translation', 'product_category_name'),
    ]
    for child, ck, parent, pk in relations:
        if child in data and parent in data:
            parents = {r.get(pk) for r in data[parent] if r.get(pk)}
            report['relationships'][f'{child}.{ck}->{parent}.{pk}'] = {
                'orphan_rows_excluding_blank': sum(bool(r.get(ck)) and r.get(ck) not in parents for r in data[child])
            }
    if 'orders' in data:
        rows = data['orders']
        report['order_status_counts'] = dict(Counter(r.get('order_status') for r in rows))
        report['order_date_ranges'] = {}
        for c in ['order_purchase_timestamp', 'order_approved_at', 'order_delivered_customer_date', 'order_estimated_delivery_date']:
            values = [r[c] for r in rows if r.get(c)]
            report['order_date_ranges'][c] = {'min': min(values) if values else None, 'max': max(values) if values else None}
        eligible = late = negative = malformed = missing = 0
        for r in rows:
            if r.get('order_status') != 'delivered':
                continue
            if not r.get('order_delivered_customer_date') or not r.get('order_estimated_delivery_date'):
                missing += 1
                continue
            try:
                actual = datetime.fromisoformat(r['order_delivered_customer_date'])
                estimate = datetime.fromisoformat(r['order_estimated_delivery_date'])
                purchase = datetime.fromisoformat(r['order_purchase_timestamp'])
            except (ValueError, KeyError, TypeError):
                malformed += 1
                continue
            eligible += 1
            late += actual.date() > estimate.date()
            negative += actual < purchase
        report['delivery_checks'] = {'eligible_orders': eligible, 'late_orders_calendar_date': late,
            'delivered_missing_delivery_dates': missing, 'malformed_required_dates': malformed,
            'negative_purchase_to_delivery': negative}
    if 'reviews' in data:
        counts = Counter(r.get('order_id') for r in data['reviews'])
        report['review_checks'] = {'orders_with_multiple_rows': sum(n > 1 for n in counts.values()),
            'score_counts': dict(Counter(r.get('review_score') for r in data['reviews']))}
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'data_quality_profile.json'
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Wrote {target}')
    for name, entry in report['tables'].items():
        print(f"{name}: {entry.get('rows', entry.get('error'))}")


if __name__ == '__main__':
    main()
