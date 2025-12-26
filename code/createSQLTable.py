__author__ = 'Maayan'
import json
import sqlite3
connection_sql = sqlite3.connect("../data/SatDatabase.db")
cursor_obj = connection_sql.cursor()

#right now I will make it for the format we created in our program. If I have more time, I will change it to be more general.
# add param to the list. remember you will need to create a new table if you change it (take the raws and continue from there).


types = {
    "uint": "UNSIGNED INT", # in sql you don't have unsigned. and because I don't do stuff with it but store it we make it text.
    "int": "INT",
    "ushort": "UNSIGNED SHORT",
    "short": "SHORT",
    "unixtime": "TIMESTAMP", #will give integer.
    "float": "FLOAT",
    "byte": ["CHAR(1)", "TEXT"], #enum is TEXT, not enum is char(1)
    "string": "TEXT",
    "double": "DOUBLE"
}
#raw is in Hex.
def type_of_param(param):
    """
    in case we have an enum we want to save in the server the text and not the byte val.
    :param param: the dict from the json.
    :return: type of param that will be written int the SQL.
    """
    try:
        if param["type"] == "byte":
            # enum need text because we will do the decoding but normal will need 1 byte
            if "enum" in param.keys(): return types["byte"][1]
            return types["byte"][0]
        return types[param["type"]]
    except KeyError or Exception:
        print("not have type field or an unknown type. can see in documents the correct types.")
        raise TypeError("CantGetParams")


def make_params_for_table(format_file):
    """
    take from the file the json and because we have only on type of subtype in this program
    we take all the params and make them fit to add to the creation of the json file.
    :param format_file: the json file we get from the config
    :param prime_key: normally the timestamp of the sat, the name of the param from config
    :return: string of the params for the creation of the SQL.
    """
    params = []
    try:
        with open(format_file, 'r') as file:
            data = json.load(file)
    except FileNotFoundError or OSError:
        print("an unknown file. (maybe not in the correct folder. need to be in jsons.")
        raise TypeError("CantGetParams")
    try:
        prime_key = data["settings"]["prime_key"]
        data = data["subType"]["params"]
    except KeyError:
        print("don't have the needed main tags (settings, prime_key, subtype or params)")
        raise TypeError("CantGetParams")
    for param in data: #maybe check if there is a way we will write in little endian
        try:
            if param["type"] == "byte" and "enum" in param.keys(): pass #need to add here something on the enum.
        except KeyError:
            print("don't have the main things in the define of the parameter. \n(not knowing which. need to check were you don't have name or type)")
            raise TypeError("CantGetParams")
        #add parameter to the string according to how it will look in the SQL creation. including primary key.
        params.append(f"{param['name']} {type_of_param(param) + " PRIMARY KEY" if param['name'] == prime_key else type_of_param(param)}")
        if param['name'] == prime_key and param["type"] != "unixtime": print("know that the primary key you chose is not time so it may cause problems later")
    return " NOT NULL,\n".join(params + ["raw TEXT NOT NULL"])

def create_tables():
    """
    going over each sat in config and create the table for who is not already there.
    """
    try:
        with open(r'..\jsons\config.json', 'r') as file:
            data = json.load(file)
    except OSError: print("you don't have the config file or it's not in the right folder.")
    for x in data:
        #for each sat in data
        try: table_name = data[x]["tableName"]
        except KeyError:
            print("you don't have table name tag in config.")
            break
        try:
            params = make_params_for_table(rf"..\jsons\{data[x]['beacon_json']}")
        except KeyError or Exception:
            print("you have a problem in params or don't have a necessary in config.")
            break
        sql_query = f"CREATE TABLE IF NOT EXISTS {table_name} (\n{params});"
        try:
            cursor_obj.execute(sql_query)
            print(f"Table, {table_name}, is Ready")
        except Exception as e: print(f"had an exception '{e}' in creating table.")

    connection_sql.close()

def main():
    create_tables()

if __name__ == "__main__":
    main()
