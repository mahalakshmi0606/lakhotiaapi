import pymysql
try:
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='jaikeerthi07a',
        database='lakhotia'
    )
    print("Connection successful")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
