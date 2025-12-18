__author__ = 'Maayan'
import json
import sqlite3
connection_sql = sqlite3.connect("../data/SatDatabase.db")
cursor_obj = connection_sql.cursor()

#right now I will make it for the format we created in our program. If I have more time, I will change it to be more general.


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
    if param["type"] == "byte":
        if "enum" in param.keys(): return types["byte"][1]
        return types["byte"][0]
    return types[param["type"]]

def make_params_for_table(format_file, prime_key):
    """
    take from the file the json and because we have only on type of subtype in this program
    we take all the params and make them fit to add to the creation of the json file.
    :param format_file: the json file we get from the config
    :param prime_key: normally the timestamp of the sat, the name of the param from config
    :return: string of the params for the creation of the SQL.
    """
    params = []
    with open(format_file, 'r') as file:
        data = json.load(file)
    data = data["subType"]["params"]
    for param in data: #maybe check if there is a way we will write in little endian
        if param["type"] == "byte" and "enum" in param.keys(): pass #need to add here something on the enum.
        params.append(f"{param['name']} {type_of_param(param) + " PRIMARY KEY" if param['name'] == prime_key else type_of_param(param)}")
    return " NOT NULL,\n".join(params + ["raw TEXT NOT NULL"])

def main():
    """
    going over each sat in config and create the table for who is not already there.
    """
    with open(r'..\jsons\config.json', 'r') as file:
        data = json.load(file)
    for x in data:
        table_name = data[x]["tableName"]
        params = make_params_for_table(rf"..\jsons\{data[x]['beacon_json']}", data[x]["primeKey"])
        sql_query = f"CREATE TABLE IF NOT EXISTS {table_name} (\n{params});"
        cursor_obj.execute(sql_query)
        print(f"Table, {table_name}, is Ready")

    connection_sql.close()

if __name__ == "__main__":
    main()
