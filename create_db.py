import pymysql
try:
    # Connect without database specified
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='jaikeerthi07a'
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS lakhotia")
    print("Database 'lakhotia' created successfully or already exists.")
    conn.close()
except Exception as e:
    print(f"Error creating database: {e}")
