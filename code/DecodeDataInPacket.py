__author__ = 'Maayan'
import json, threading, sqlite3, requests
import time, csv
from struct import unpack
from datetime import datetime

from createSQLTable import create_tables
connection_sql = sqlite3.connect("../data/SatDatabase.db")
connection_sql.row_factory = sqlite3.Row

#make the start dictionaries
def get_norad_id(satellites_name):
    norad_id = []
    url = f"https://db.satnogs.org/api/satellites/?search&format=json"
    response = requests.get(url)
    data = response.json()
    for sat in data:
        if sat['name'] in satellites_name:
            norad_id.append({"satName": sat['name'], "noradId": sat['norad_cat_id']})
    return norad_id
def make_dicts_according_to_config():
    try:
        with open(r'..\jsons\config.json', 'r') as file:
            data = json.load(file)
    except OSError:
        print("you don't have the config file or it's not in the right folder.")
        raise TypeError("Can't make it work, need change")
    sats = {}
    jsons = {}
    sat_ids = []
    for x in data:
        #for each sat in data
        try:
            table_name = data[x]["tableName"]
            callsign = data[x]["callsign"]
            format_json = data[x]['beacon_json']
            sat_ids.append(data[x]["satnogs_name"]) #here need to put from the chat the ids.
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
    try:
        sat_ids = get_norad_id(sat_ids)
    except Exception as e:
        print(f"had a problem: {e}")
        raise TypeError("Can't make it work, need change")
    return sats, jsons, sat_ids
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
SATELLITES, JSONS, SatIds = make_dicts_according_to_config()
try:
    JSONS_FOR_HTML = jsons_for_html(JSONS)
except KeyError or Exception:
    print("you have a problem in one of the normal jsons, fix it (it was fine while the table created first)")
    raise TypeError("problem in json")

#used in server
def create_options():
    ret = ""
    for sat in SATELLITES:
        ret += f"<option>{sat}</option>\n\t\t\t"
    return ret

def make_for_html(sat_name, last_date, top):
    """
    take from SQL and put it in the format for the html. it's added to what I already have.
    :param sat_name: name of sat as written in SATELLITES
    :param last_date: in time unix. say from where I need to take. (as time come)
    :param top: is for the top of the page or for the bottom. according to that I know if I gave the min I have or the max
    :return: build for html, min_date, max_date <- know what to take according to top or bottom.
    """
    #last date is in unix format. (int)
    sat: dict = SATELLITES[sat_name]
    sql_query = f"SELECT * FROM {sat['table_name']} WHERE {JSONS_FOR_HTML[sat['json']]['primaryKey']} {'>' if top else '<'} {last_date} ORDER BY {JSONS_FOR_HTML[sat['json']]['primaryKey']} DESC LIMIT 25"
    with sat["threadLock"]:
        sat["cursor"].execute(sql_query)
        data = sat["cursor"].fetchall()
    html_code = ""
    json_sorted = dict(sorted(JSONS_FOR_HTML[sat['json']].items()))
    time_params = json_sorted["time_param"]
    primary = json_sorted["primaryKey"]
    del json_sorted["primaryKey"], json_sorted["time_param"]
    for row in data:
        html_code += f'<div class="containerPacket">\n<div class="divRaw">\n<div style="text-align: center"><u><b>Hex raw:</b></u></div>\n{row["raw"].upper()}</div>\n'
        for i in range(1, len(json_sorted) // 5 + 1):
            html_code += '<div class="container">\n'
            for k in range(5):
                html_code += f'<div class="containerSub">\n<div class="titleSub">{list(json_sorted.keys())[i*k]}</div>\n<hr />\n'
                for param_name in json_sorted[list(json_sorted.keys())[i*k]]:
                    html_code += f'<u>{param_name}:</u> {row[param_name] if param_name not in time_params else datetime.fromtimestamp(row[param_name]).strftime("%d.%m.%Y %H:%M:%S")}<br />\n'
                html_code += '</div"></div>\n'
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
    if not data: return "", last_date, last_date
    return html_code, data[-1][primary], data[0][primary]




#here I have the with lock while in the loop it will be different.
"""
todo: I will do here everything that is reading the jsons and etc. there is stuff that I will need
them to be in main server but general stuff, making the packet, getting it and cleaning it up will
be here. It's not that much but I want the loop that read from the SatNogs and put in SQL to be here.
And also the creation because I want it to be arrange. 

Need to check how to take from satNogs and according to that I will know more.
"""

#for the infinite loop that reads from the satnogs. it may be class or not, I still need to deside on that.

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
    if data_type == "string": return data_bytes.decode("utf-8")
    if data_type == "byte": return unpack(('>' if is_big else '<') + "c", data_bytes)[0]
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
    i = 8 #where in the packet we start. (where the params are) again it's only for our sats.
    decode_to_sql = [] #in hope
    bytes_from_data = 0
    for param in json_params:
        if param["type"] != "string":
            bytes_from_data = data[i: i + SIZE_IN_BYTES[param["type"]]]
            i += SIZE_IN_BYTES[param["type"]]
        else:
            bytes_from_data = data[i: i + data[i:].indexof(0x00)]
            i += data[i:].indexof(0x00)
        if "isBigEndian" in param.keys():
            to_append = decoded_param(bytes_from_data, param["type"], param["isBigEndian"])
        else:
            to_append = decoded_param(bytes_from_data, param["type"], default_endian)
        if param["type"] == "byte" and "enum" in param.keys():
            to_append = doing_format(to_append, "byte", param["enum"])
        elif "format" in param.keys():
            to_append = doing_format(to_append, param["type"], param["format"])
        decode_to_sql.append(to_append)
    decode_to_sql.append(data.hex())
    return decode_to_sql

class SatNogsToSQL:
    def __init__(self, newest_dates=None):
        if not newest_dates: self.newest_dates = {sat: "2000-01-01T00:00:00+00:00" for sat in SATELLITES}
        else: self.newest_dates = newest_dates
        token = '935188971e64257d0736b4f89f575791312226fb' #todo: need to find a way to make it permeate
        self.__headers = {'Authorization': f'Token {token}'}
        self.run = True

    def check_packet(self, packet, timestamp):
        frame = bytes.fromhex(packet)
        src = frame[:7]
        frame = frame[16:]
        callsign = ''.join(chr(b >> 1) for b in src[:6])
        if callsign not in [SATELLITES[sat]["callsign"] for sat in SATELLITES]: return False, ["", ""]
        sat_name = [sat for sat in SATELLITES if callsign == SATELLITES[sat]["callsign"]][0]
        if datetime.fromisoformat(timestamp.replace("Z", "+00:00")) <= datetime.fromisoformat(self.newest_dates[sat_name]): return False, ["time", ""]
        if frame[4:6] != bytes.fromhex(JSONS[SATELLITES[sat_name]["json"]]["settings"]["opcode"]): return False, ["", ""]
        return True, [sat_name, frame]

    def enter_packets(self, packets):
        results = packets["results"]
        ret_val = "fine"
        for res in results:
            ret = self.check_packet(res["frame"], res["timestamp"])
            if not ret[0]:
                if ret[1][0] != "time": continue
                else:
                    ret_val = "time"
                    break
            sat_name, packet = ret[1]
            json_file = JSONS[SATELLITES[sat_name]["json"]]
            values = decode_data_for_sql(packet, json_file["subType"]["params"], not json_file["settings"]["isDefaultLittleEndian"])
            sql_query = f"INSERT OR IGNORE INTO {SATELLITES[sat_name]['table_name']} VALUES ({" ,".join([str(x) if type(x) != str else f"'{x}'" for x in values])});"
            with SATELLITES[sat_name]["threadLock"]:
                SATELLITES[sat_name]["cursor"].execute(sql_query)
        connection_sql.commit()
        return str(datetime.fromisoformat(results[0]["timestamp"].replace("Z", "+00:00"))), ret_val  # need to add the check for the time. when I get there I should stop the loop and only do what's before. (by if == then)


    def infinite_loop(self):
        try:
            while self.run:
                for norad_id in SatIds:
                    url = f"https://db.satnogs.org/api/telemetry/?satellite={norad_id["noradId"]}"
                    response = requests.get(url, headers=self.__headers)
                    data = response.json()
                    self.newest_dates[norad_id["satName"]], val = self.enter_packets(data)
                    if val == "time": continue
                    while data["next"]:
                        response = requests.get(data["next"], headers=self.__headers)
                        data = response.json()
                        val = self.enter_packets(data)
                        if val[1] == "time": break
                        time.sleep(45)
                    time.sleep(120)
            time.sleep(7200) # 2 hours.
        finally:
            with open("../jsons/newestTime.json", "w") as file: file.write(json.dumps(self.newest_dates))

    # def infinite_loop(self):
    #     with open("../data/Tevel19.csv", newline="", encoding="utf-8") as f:
    #         reader = csv.reader(f)
    #         count = 0
    #         data = {"results": []}
    #         for row in reader:
    #             row = row[0]
    #             if len(data["results"]) >= 25:
    #                 self.enter_packets(data)
    #                 data["results"] = []
    #             data_mini = row.split("|")[:2]
    #             data["results"].append({"timestamp": f"{data_mini[0].replace(" ", "T")}Z", "frame": data_mini[1]})



def main():
    create_tables()
    with open("../jsons/newestTime.json", "r") as file:
        packets_to_sql = SatNogsToSQL(json.load(file))
    packets_to_sql.infinite_loop()

    #check it.


if __name__ == "__main__":
    try:
        main()
    finally: connection_sql.close()
