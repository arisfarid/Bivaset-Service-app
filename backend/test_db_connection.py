#!/usr/bin/env python3

import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='bivaset_db',
        user='bivaset_user',
        password='bivaset123'
    )
    print('Database connection successful!')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM django_content_type;')
    count = cursor.fetchone()[0]
    print(f'Found {count} content types in database')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
