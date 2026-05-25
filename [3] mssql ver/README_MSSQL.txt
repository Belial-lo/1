Версия для Microsoft SQL Server.

Что изменено:
- schema.sql написан на T-SQL.
- SERIAL заменен на IDENTITY(1,1).
- VARCHAR заменен на NVARCHAR.
- PostgreSQL ON CONFLICT заменен на IF NOT EXISTS.
- import_excel.py использует pyodbc вместо psycopg2.
- параметры SQL-запросов используют ? вместо %s.

Что установить:
pip install pyodbc openpyxl

Также нужен ODBC Driver for SQL Server.
Если драйвер называется иначе, поменяй строку в import_excel.py:
"driver": "{ODBC Driver 17 for SQL Server}"

Порядок запуска:
1. В SQL Server Management Studio создать базу DB_Ivah.
2. Выполнить schema.sql в базе DB_Ivah.
3. Запустить:
python import_excel.py

Если SQL Server не подключается через Windows-авторизацию,
замени connection_string в import_excel.py на вариант с логином и паролем.
