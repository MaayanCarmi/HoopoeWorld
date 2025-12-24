__author__ = 'Maayan'
import json, threading, sqlite3
from struct import unpack
from datetime import datetime
connection_sql = sqlite3.connect("../data/SatDatabase.db")
connection_sql.row_factory = sqlite3.Row
def make_dicts_according_to_config():
    try:
        with open(r'..\jsons\config.json', 'r') as file:
            data = json.load(file)
    except OSError:
        print("you don't have the config file or it's not in the right folder.")
        raise TypeError("Can't make it work, need change")
    sats = {}
    jsons = {}
    for x in data:
        #for each sat in data
        try:
            table_name = data[x]["tableName"]
            callsign = data[x]["callsign"]
            format_json = data[x]['beacon_json']
            sats[x] = {"table_name": table_name, "callsign": callsign,
                       "json": format_json, "threadLock": threading.Lock(),
                       "cursor": connection_sql.cursor()}
            if format_json not in jsons.keys():
                with open(rf'..\jsons\{format_json}', 'r') as file:
                    jsons[format_json] = json.load(file)
                    try:
                        jsons[format_json]["settings"]["opcode"]
                    except KeyError:
                        print("you don't have opcode in json file.")
                        raise TypeError("Can't make it work, need change")
        except KeyError:
            print("you don't have all the needed tags in config.")
            raise TypeError("Can't make it work, need change")
        except OSError:
            print("you don't have this file in the folder.")
            raise TypeError("Can't make it work, need change")
    return sats, jsons
def jsons_for_html(json_format):
    """
    take from the json the needed params and make from them the subSystem it's from.
    when we are really entering stuff we check 2 things. 1. if raw, 2. where is it here.
    :param json_format: all the formats as jsons and needed to change them.
    :return: jsons but for the html
    """
    jsons = {
    }
    counter = {}
    for x in json_format:
        jsons[x] = {"primaryKey": json_format[x]["settings"]["prime_key"]}
        parameters = json_format[x]["subType"]["params"]
        are_unix = []
        for param in parameters:
            if param["type"] == "unixtime": are_unix.append(param["name"])
            if "subSystem" in param.keys():
                if param["subSystem"] not in jsons[x]:
                    jsons[x][param["subSystem"]] = [param["name"]]
                elif counter[param["subSystem"]] < 10:
                    jsons[x][param["subSystem"]].append(param["name"])
                else:
                    if counter[param["subSystem"]] % 10 == 0: jsons[x][param["subSystem"] + f" {str(counter[param["subSystem"]] // 10)}"] = [param["name"]]
                    else: jsons[x][param["subSystem"] + f" {str(counter[param["subSystem"]] // 10)}"].append(param["name"])
                counter[param["subSystem"]] = counter[param["subSystem"]] + 1 if param["subSystem"] in counter.keys() else 1
            else:
                if "General" not in jsons[x]:
                    jsons[x]["General"] = [param["name"]]
                elif counter["General"] < 10:
                    jsons[x]["General"].append(param["name"])
                else:
                    if counter["General"] % 10 == 0:
                        jsons[x][f"General {str(counter["General"] // 10)}"] = [param["name"]]
                    else:
                        jsons[x][f"General {str(counter["General"] // 10)}"].append(param["name"])
                counter["General"] = counter["General"] + 1 if "General" in counter.keys() else 1
        jsons[x]["time_param"] = are_unix #because I will need to change it to normal after.
    return jsons
SATELLITES, JSONS = make_dicts_according_to_config()
JSONS_FOR_HTML = jsons_for_html(JSONS)



def make_for_html(sat: dict, last_date, top):
    """
    take from SQL and put it in the format for the html. it's added to what I already have.
    :param sat: name of sat as written in SATELLITES
    :param last_date: in time unix. say from where I need to take. (as time come)
    :param top: is for the top of the page or for the bottom. according to that I know if I gave the min I have or the max
    :return: build for html, min_date, max_date <- know what to take according to top or bottom.
    """
    #last date is in unix format. (int)
    sql_query = f"SELECT * FROM {sat['tableName']} WHERE {JSONS_FOR_HTML[sat['format_json']]['primaryKey']} {'>' if top else '<'} {last_date} ORDER BY {JSONS_FOR_HTML[sat['format_json']]['primaryKey']} DESC LIMIT 25"
    with sat["threadLock"]:
        sat["cursor"].execute(sql_query)
        data = sat["cursor"].fetchall()
    html_code = ""
    json_sorted = dict(sorted(JSONS_FOR_HTML[sat['format_json']].items()))
    time_params = json_sorted["time_param"]
    primary = json_sorted["primaryKey"]
    del json_sorted["primaryKey"], json_sorted["time_param"]
    for row in data:
        html_code += f'<div class="containerPacket" style="margin-top: 6%">\n<div class="divRaw">\n<div style="text-align: center"><u><b>Hex raw:</b></u></div>\n{row["raw"]}</div>\n'
        for i in range(1, len(json_sorted) // 5 + 1):
            html_code += '<div class="container">\n'
            for k in range(5):
                html_code += f'<div class="containerSub">\n<div class="titleSub">{list(json_sorted.keys())[i*k]}</div>\n<hr />\n'
                for param_name in json_sorted[list(json_sorted.keys())[i*k]]:
                    html_code += f'<u>{param_name}:</u> {row[param_name] if param_name not in time_params else datetime.fromtimestamp(row[param_name]).strftime("%d.%m.%Y %H:%M:%S")}<br />\n'
                html_code += '</div">\n'
            html_code += '</div>\n'
            if len(json_sorted) % 5 != 0 and i == (len(json_sorted) // 5):
                html_code += '<div class="container">\n'
                for k in range(len(json_sorted) % 5):
                    html_code += f'<div class="containerSub">\n<div class="titleSub">{list(json_sorted.keys())[i * k]}</div>\n<hr />\n'
                    for param_name in json_sorted[list(json_sorted.keys())[i * k + 5]]:
                        html_code += f'<u>{param_name}:</u> {row[param_name] if param_name not in time_params else datetime.fromtimestamp(row[param_name]).strftime("%d.%m.%Y %H:%M:%S")}<br />\n'
                    html_code += '</div">\n'
                html_code += '</div>\n'
        html_code += '</div>\n'
    return html_code, data[-1][primary], data[0][primary]



#todo maybe I will change it to be in the server and I will call the function there. in second thouh no
#todo because it will be needing threads and a lock so I will need to have him. (I think I will make a lock on each sat diffrently (and only on the SQL).
#here I have the with lock while in the loop it will be different.
"""
todo: I will do here everything that is reading the jsons and etc. there is stuff that I will need
them to be in main server but general stuff, making the packet, getting it and cleaning it up will
be here. It's not that much but I want the loop that read from the SatNogs and put in SQL to be here.
And also the creation because I want it to be arrange. 

        elif param["type"] == "unixtime":
            to_append = doing_format(to_append, "unixtime", None)
    if data_type == "unixtime":
        return datetime.fromtimestamp(data).strftime("%d.%m.%Y %H:%M:%S")

Need to check how to take from satNogs and according to that I will know more.
"""


SIZE_IN_BYTES = {
    "uint": 4, # we read 4 and then change to text.
    "int": 4,
    "ushort": 2,
    "short": 2,
    "unixtime": 4, #will give integer.
    "float": 4,
    "byte": 1, #enum is TEXT, not enum is char(1)
    "string": 250, #need to check when we have the first 00, and according to that we know. that's the max written here.
    "double": 8
}

def doing_format(data, data_type, format_data):
    if data_type == "byte": return format_data[chr(ord(data) + 0x30)]
    if data_type in ["short", "ushort", "uint", "float", "double", "int"]:
        #pass #todo: need to create the way for format.
        return data

def decoded_param(data_bytes, data_type, is_big):
    if data_type == "byte": return unpack(('>' if is_big else '<') + "c", data_bytes)[0]
    if data_type == "string": return unpack(('>' if is_big else '<') + "s", data_bytes)[0]
    if data_type == "short": return unpack(('>' if is_big else '<') + "h", data_bytes)[0]
    if data_type == "uint": return unpack(('>' if is_big else '<') + "I", data_bytes)[0]
    if data_type == "ushort": return unpack(('>' if is_big else '<') + "H", data_bytes)[0]
    if data_type == "float": return unpack(('>' if is_big else '<') + "f", data_bytes)[0]
    if data_type == "double": return unpack(('>' if is_big else '<') + "d", data_bytes)[0]
    if data_type in ["int", "unixtime"]: return unpack(('>' if is_big else '<') + "i", data_bytes)[0]

def decode_data_for_sql(data, json_params, default_endian):
    """
    getting parameters and by them making the params that needed to create the INSERT to the SQL.
    :param data: Hex that is only from the data section of Ax25
    :param json_params: according to what we will learn getting the params and the type of each.
    :param default_endian: if big or little.
    :return:
    """
    i = 8*2 #where in the packet we start. (where the params are) again it's only for our sats.
    decode_to_sql = [] #in hope
    bytes_from_data = 0
    for param in json_params:
        if param["type"] != "string":
            bytes_from_data = data[i: i + SIZE_IN_BYTES[param["type"]]*2]
            i += SIZE_IN_BYTES[param["type"]]*2
        else:
            bytes_from_data = data[i: i + data[i:].indexof(0x00)*2]
            i += data[i:].indexof(0x00)*2
        bytes_from_data = bytes.fromhex(bytes_from_data)
        if "isBigEndian" in param.keys():
            to_append = decoded_param(bytes_from_data, param["type"], param["isBigEndian"])
        else:
            to_append = decoded_param(bytes_from_data, param["type"], default_endian)
        if param["type"] == "byte" and "enum" in param.keys():
            to_append = doing_format(to_append, "byte", param["enum"])
        elif "format" in param.keys():
            to_append = doing_format(to_append, param["type"], param["format"])
        decode_to_sql.append(to_append)
    decode_to_sql.append(data)
    return decode_to_sql


def main():
    #check it.
    data = JSONS["tevels_beacon.json"]
    dec = decode_data_for_sql("0000000B00018D00CA1E8013F80C7EFF660DE3FF7D0000000A00000ABD410050384100DC664100611A42007EBA410004474135F02F6900C01B470000000000A0F17700E0D530000000001200000074CF0F0000000000FFFFFFFFFFFFFFFF2BCEC822D9E483220400000000CA3640601D20690000FFFFFFFF000B00000050613A425671F941F7B17E4051F82444B2BADDC50000DDC2",data["subType"]["params"], False)

    print(dec)

if __name__ == "__main__":
    try:
        main()
    finally: connection_sql.close()
