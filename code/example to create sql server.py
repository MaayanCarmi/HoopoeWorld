import sqlite3
connection_sql = sqlite3.connect("../data/SatDatabase.db")
# cursor object
cursor_obj = connection_sql.cursor()

#todo: need to get from the json and make according to that. the json will be used to more stuff.
# here I talk only on the config json that will call the others. it's not the decryption but the
# creation of the table.

# Creating table
table = """ CREATE TABLE IF NOT EXISTS UsersTable (
            id INT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            pword TEXT NOT NULL,
            salt TEXT NOT NULL
        ); """

cursor_obj.execute(table)

print("Table is Ready")

# Close the connection
connection_sql.close()