# repl.py

from engine import DatabaseEngine

def main():
    db = DatabaseEngine()
    print("=== Mini Motor SQL ===  (escribe 'exit' para salir)\n")
    while True:
        try:
            sql = input("sql> ").strip()
            if not sql:
                continue
            if sql.lower() == 'exit':
                break
            result = db.execute(sql)
            print(result)
        except KeyboardInterrupt:
            break

if __name__ == '__main__':
    main()