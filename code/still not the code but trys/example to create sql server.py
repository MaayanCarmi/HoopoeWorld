import sqlite3
connection_sql = sqlite3.connect("../../data/SatDatabase.db")
# cursor object
cursor_obj = connection_sql.cursor()

#todo: need to get from the json and make according to that. the json will be used to more stuff.
# here I talk only on the config json that will call the others. it's not the decryption but the
# creation of the table.
types = {
    "uint": "INT",
    "int": "",
    "ushort": "",
    "short": "",
    "unixtime": "",
    "float": "",
    "byte": "",
    "string": "",
    "double": ""
}
# Creating table
table = """ CREATE TABLE IF NOT EXISTS UsersTable (
            id INT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            pword TEXT NOT NULL,
            salt TEXT NOT NULL
        ); """
dec = [7882, 4992, 3320, -130, 3430, -29, 125, 0, 10, 23.6298828125, 11.51953125, 14.4287109375, 38.5947265625, 23.3115234375, 12.4384765625, '03.12.2025 10:09:25', 1193000960, 0, 2012323840, 819322880, 0, 18, 1036148, 0, -1, -1, 583585323, 579069145, 22.789062500000014, '21.11.2025 10:05:52', 0, 4294967295, 'operational', 11, 46.59503173828125, 31.180339813232422, 3.979612112045288, 659.8799438476562, -7095.3369140625, -110.5]
table = f"""INSERT INTO Tevel11Data VALUES ({" ,".join([str(x) if type(x) != str else f"'{x}'" for x in dec])}, '0');
"""
print(table)
cursor_obj.execute(table)

print("Table is Ready")

# Close the connection
connection_sql.close()