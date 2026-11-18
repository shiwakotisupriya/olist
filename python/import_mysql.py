"""Import Olist CSVs into a NEW MySQL database without changing source files.

Install dependency: python -m pip install mysql-connector-python
Run: python A:/olist-delivery-analytics/python/import_mysql.py
Requires a running MySQL 8+ server and permission to create a database.
Password is prompted securely and is never written to disk.
An existing database is refused; interrupted imports need explicit cleanup in Workbench.
"""
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from getpass import getpass
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
TABLES = {
    'olist_orders_dataset': ['order_id','customer_id','order_status','order_purchase_timestamp','order_approved_at','order_delivered_carrier_date','order_delivered_customer_date','order_estimated_delivery_date'],
    'olist_customers_dataset': ['customer_id','customer_unique_id','customer_zip_code_prefix','customer_city','customer_state'],
    'olist_order_items_dataset': ['order_id','order_item_id','product_id','seller_id','shipping_limit_date','price','freight_value'],
    'olist_order_payments_dataset': ['order_id','payment_sequential','payment_type','payment_installments','payment_value'],
    'olist_order_reviews_dataset': ['review_id','order_id','review_score','review_comment_title','review_comment_message','review_creation_date','review_answer_timestamp'],
    'olist_products_dataset': ['product_id','product_category_name','product_name_lenght','product_description_lenght','product_photos_qty','product_weight_g','product_length_cm','product_height_cm','product_width_cm'],
    'olist_sellers_dataset': ['seller_id','seller_zip_code_prefix','seller_city','seller_state'],
    'olist_geolocation_dataset': ['geolocation_zip_code_prefix','geolocation_lat','geolocation_lng','geolocation_city','geolocation_state'],
    'product_category_name_translation': ['product_category_name','product_category_name_english'],
}
DATES = {'order_purchase_timestamp','order_approved_at','order_delivered_carrier_date','order_delivered_customer_date','order_estimated_delivery_date','shipping_limit_date','review_creation_date','review_answer_timestamp'}
MONEY = {'price','freight_value','payment_value'}
COORDS = {'geolocation_lat','geolocation_lng'}
INTEGERS = {'order_item_id','payment_sequential','payment_installments','review_score','product_name_lenght','product_description_lenght','product_photos_qty','product_weight_g','product_length_cm','product_height_cm','product_width_cm'}
KEYS = {
    'olist_orders_dataset': ['order_id'], 'olist_customers_dataset': ['customer_id'],
    'olist_order_items_dataset': ['order_id','order_item_id'],
    'olist_order_payments_dataset': ['order_id','payment_sequential'],
    'olist_products_dataset': ['product_id'], 'olist_sellers_dataset': ['seller_id'],
    'product_category_name_translation': ['product_category_name'],
}


def sql_type(column):
    if column in DATES:
        return 'DATETIME'
    if column in MONEY:
        return 'DECIMAL(12,2)'
    if column in COORDS:
        return 'DECIMAL(20,15)'
    if column in INTEGERS:
        return 'INT'
    if column.endswith('_id'):
        return 'VARCHAR(32)'
    if 'zip_code_prefix' in column:
        return 'VARCHAR(5)'
    if column.endswith('_state'):
        return 'VARCHAR(2)'
    if column.startswith('review_comment'):
        return 'TEXT'
    return 'VARCHAR(255)'


def convert(column, value):
    if value == '':
        return None
    if column in DATES:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    if column in MONEY or column in COORDS:
        number = Decimal(value)
        if not number.is_finite():
            raise ValueError('Non-finite number')
        # MySQL DECIMAL(20,15) retains Olist coordinate precision to 15 places.
        # Money must not silently round fractional cents.
        if column in MONEY and number != number.quantize(Decimal('0.01')):
            raise ValueError('Money has fractional cents')
        return number
    if column in INTEGERS:
        return int(value)
    # ZIP prefixes are identifiers; preserve the source representation as text.
    return value


def records(path, columns):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != columns:
            raise ValueError(f'Unexpected columns in {path.name}: {reader.fieldnames}')
        for line, row in enumerate(reader, 2):
            if None in row or any(row[c] is None for c in columns):
                raise ValueError(f'Unexpected CSV field count in {path.name}, record {line}')
            try:
                yield tuple(convert(c, row[c]) for c in columns)
            except (ValueError, InvalidOperation) as error:
                raise ValueError(f'Invalid field in {path.name}, record {line}: {error}') from error


def main():
    try:
        import mysql.connector
    except ImportError:
        sys.exit('First run: python -m pip install mysql-connector-python')
    paths, counts = {}, {}
    print('Checking every CSV before connecting; geolocation may take a minute.')
    for table, columns in TABLES.items():
        matches = list(RAW.rglob(table + '.csv'))
        if len(matches) != 1:
            sys.exit(f'Expected one {table}.csv under {RAW}; found {len(matches)}')
        paths[table] = matches[0]
        counts[table] = sum(1 for _ in records(matches[0], columns))
        print(f'Validated {table}: {counts[table]:,} rows')
    host = input('MySQL host [localhost]: ').strip() or 'localhost'
    port = int(input('MySQL port [3306]: ').strip() or '3306')
    user = input('MySQL username [root]: ').strip() or 'root'
    database = input('NEW database name [olist_analytics]: ').strip() or 'olist_analytics'
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', database):
        sys.exit('Use a database name starting with a letter, then letters, numbers or underscores.')
    connection = mysql.connector.connect(host=host, port=port, user=user,
        password=getpass('MySQL password: '), charset='utf8mb4')
    cursor = connection.cursor()
    try:
        cursor.execute('SELECT VERSION()')
        version = cursor.fetchone()[0]
        if 'MariaDB' in version or int(version.split('.')[0]) < 8:
            sys.exit(f'MySQL 8+ is required for the project SQL; server reports {version}')
        cursor.execute('SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s', (database,))
        if cursor.fetchone():
            sys.exit('Database already exists. Choose a new database name; nothing was overwritten.')
        cursor.execute(f'CREATE DATABASE `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_bin')
        cursor.execute(f'USE `{database}`')
        cursor.execute("SET SESSION sql_mode = 'STRICT_ALL_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,ONLY_FULL_GROUP_BY'")
        for table, columns in TABLES.items():
            definitions = [f'`{c}` {sql_type(c)}' for c in columns]
            if table in KEYS:
                definitions.append('PRIMARY KEY (' + ','.join(f'`{c}`' for c in KEYS[table]) + ')')
            if 'order_id' in columns and table != 'olist_orders_dataset':
                if table not in KEYS or KEYS[table][0] != 'order_id':
                    definitions.append('INDEX (`order_id`)')
            cursor.execute(f'CREATE TABLE `{table}` (' + ','.join(definitions) + ') ENGINE=InnoDB')
            insert = f'INSERT INTO `{table}` (' + ','.join(f'`{c}`' for c in columns) + ') VALUES (' + ','.join(['%s'] * len(columns)) + ')'
            batch = []
            for row in records(paths[table], columns):
                batch.append(row)
                if len(batch) == 1000:
                    cursor.executemany(insert, batch)
                    connection.commit()
                    batch.clear()
            if batch:
                cursor.executemany(insert, batch)
                connection.commit()
            cursor.execute(f'SELECT COUNT(*) FROM `{table}`')
            actual = cursor.fetchone()[0]
            if actual != counts[table]:
                raise RuntimeError(f'Row-count mismatch for {table}: expected {counts[table]}, got {actual}')
            print(f'Imported and reconciled {table}: {actual:,} rows')
        print(f'Import complete. In Workbench run: USE `{database}`;')
        print('Then execute sql/02_reporting_views.sql followed by sql/03_validation.sql.')
    except Exception:
        connection.rollback()
        print(f'Import stopped. Database {database} may contain partial tables; nothing is deleted automatically.')
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == '__main__':
    main()
