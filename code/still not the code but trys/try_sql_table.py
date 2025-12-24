__author__ = 'Maayan'
import sqlite3

def main():
    conn = sqlite3.connect(r"C:\Users\maaya\Downloads\cyber.db")

    # Set the row_factory to sqlite3.Row or a custom function
    conn.row_factory = sqlite3.Row
    # Alternatively, for a list of dictionaries:
    # conn.row_factory = lambda cursor, row: {col[0]: row[i] for i, col in enumerate(cursor.description)}

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cyber")

    results = cursor.fetchall()

    # Now you can access data by column name
    for row in results:
        print(dict(row))

        # To get just the column names
    column_names = [description[0] for description in cursor.description]
    print(column_names)

    conn.close()


if __name__ == "__main__":
    main()
