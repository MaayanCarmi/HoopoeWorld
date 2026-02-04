__author__ = 'Maayan'
import json, threading, sqlite3, requests, math, os
import time, csv, io
from struct import unpack
from datetime import datetime
import pandas as pd
from createSQLTable import create_tables

# I think I make enough checks to make sure it won't be at the same time in both function
connection_sql = sqlite3.connect("../data/SatDatabase.db", check_same_thread=False)
connection_sql.row_factory = sqlite3.Row

#make the start dictionaries, stuff I want to have at all time, so I won't need to read the json all the time.
def check_make_formula(formula):
    """
    take the given format (format is the formula) check it's fine and return the clean one if possible.
    :param formula: format of a number (all types: short, int, float etc.)
    :return: error on a problem
            the clean formula on success.
    """
    formula = formula.replace(" ", "").lower()
    if formula.count("x") == 0:
        raise TypeError("Incorrect format, you need to have at lest one x")
    count_open = 0
    f = 0
    while f < len(formula):
        if not formula[f].isdigit() and formula[f] not in "x()-+%*/": #check we don't have an unknown char
            raise TypeError("Incorrect format, have invalid chars.")
        if formula[f] == "(": count_open += 1 #so in the end we can check that all the parentheses are closed
        elif formula[f] == ")" and count_open == 0: #make sure we have closer only when needed
            raise TypeError("Incorrect format, you have more ) then (")
        elif formula[f] == ")": count_open -= 1 #same as with the add one when (
        if f != 0: #because we check before (on f-1)
            if formula[f] == "(" and formula[f-1] == ".": #not ".("
                raise TypeError("Incorrect format, you have dot in before parentheses")
            elif formula[f] == ")" and formula[f-1] in "*/-+%": #not "+)" or "*)" etc.
                raise TypeError("Incorrect format, the format is not finished")
            elif formula[f] == "(" and formula[f-1] not in "*/-+%(": #to add * if it possible
                try: formula = formula[:f] + "*(" + formula[f+1:]
                except IndexError: raise TypeError("Incorrect format, the format is not finished.") #if we don't have next
                f += 1
        f += 1
    if count_open != 0: #no have open parentheses
        raise TypeError("Incorrect format, you don't close all the parentheses")
    if formula[-1] in "*/%(.": #format finished
        raise TypeError("Incorrect format, the format is not finished.")

    return formula
def get_norad_id(satellites_name):
    """
    get from the SatNogs website the norad IDs that I will need to get to the satellites.
    :param satellites_name: a list that have all the satNogs names of the satellites (that are in the config).
    :return: list of dicts of satName and his noradID.
    """
    norad_id = []
    url = f"https://db.satnogs.org/api/satellites/?search&format=json"
    response = requests.get(url) #get all the norad IDs in satNogs
    data = response.json()
    for sat in data:
        if sat['name'] in satellites_name: #find the relevant ones
            norad_id.append({"satName": sat['name'], "noradId": sat['norad_cat_id']})
    return norad_id

def make_dicts_according_to_config():
    """
    get all the jsons (config and the ones of format) and put them in a dict, check them and other.
    :return: sats, jsons, satIds.
            sats - dict of dicts, name of sat and a few params, some are from json and some are from the code.
            jsons - also dict of dicts, have the format jsons, so I won't have it more than ones to each json.
            satIds - list of dicts, what we get from get_norad_id
    """
    try:
        with open(r'..\jsons\config.json', 'r') as file: #open config
            data = json.load(file)
    except OSError:
        raise TypeError("Can't make it work, You don't have the config file or it's not in the right folder.")
    sats = {}
    jsons = {}
    sat_ids = []
    for x in data:
        #for each sat in data (x is the sat name)
        try:
            table_name = data[x]["tableName"] #name of SQL table.
            callsign = data[x]["callsign"] #callsign of sat
            format_json = data[x]['beacon_json'] #which file is the format
            sat_ids.append(data[x]["satnogs_name"]) #here need to put from the chat the ids.
            sats[x] = {"table_name": table_name, "callsign": callsign,
                       "json": format_json, "satnogs": sat_ids[-1], "threadLock": threading.Lock(),
                       "cursor": connection_sql.cursor()} #make the dict, also have a threadLock and cursor for each sat.
            if format_json not in jsons.keys(): #if we don't already have it
                with open(rf'..\jsons\{format_json}', 'r') as file: #try open if error have an exception.
                    jsons[format_json] = json.load(file)
                    try:
                        setting = jsons[format_json]["settings"] #check we have an opcode.
                        setting["opcode"] = setting["opcode"]
                        setting["sizeof_header"] = setting["sizeof_header"]
                        setting["place_start_opcode"] = setting["place_start_opcode"]
                    except KeyError: raise TypeError(f"Can't make it work, Don't have opcode or all the headers in json file ({format_json})")
                    except Exception as e: raise TypeError(f"Can't make it work, need to be int here: {format_json}")
                    try: #make sure we have subType and params, also if you have format make it to work.
                        new_params = []
                        for param in jsons[format_json]["subType"]["params"]:
                            if "format" in param.keys():
                                param["format"] = check_make_formula(param["format"])
                            new_params.append(param)
                        jsons[format_json]["subType"]["params"] = new_params
                    except KeyError:
                        raise TypeError(f"Can't make it work, Don't have params or subType in json file ({format_json})")
        except KeyError:
            raise TypeError("Can't make it work, Don't have all the needed tags in config.")
        except OSError:
            raise TypeError("Can't make it work, You don't have this file in the jsons folder")
    try:
        sat_ids = get_norad_id(sat_ids)
    except Exception as e:
        raise TypeError(f"Can't make it work, had a problem: {e}")
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
    counter = {} #make sure we don't have more than 10 in subsystem
    for x in json_format: #doing it to each format.
        jsons[x] = {"primaryKey": json_format[x]["settings"]["prime_key"]} #keep the primary key
        parameters = json_format[x]["subType"]["params"] #get all the params to sort.
        are_unix = [] #save all the params that are time. (because I will need it after)
        for param in parameters: # going through the params
            if param["type"] == "unixtime": are_unix.append(param["name"]) #check if we are time param and if so add.
            if "subSystem" in param.keys(): #check if there is this tag.
                if param["subSystem"] not in jsons[x]: #add subSystem if not exist
                    jsons[x][param["subSystem"]] = [param["name"]]
                elif counter[param["subSystem"]] < 10: #if we have less than 10.
                    jsons[x][param["subSystem"]].append(param["name"])
                else: #if more...
                    #it will do something like that: if you have more than 10 in "EPS" it will be "EPS 1" etc.
                    if counter[param["subSystem"]] % 10 == 0: jsons[x][param["subSystem"] + f" {str(counter[param["subSystem"]] // 10)}"] = [param["name"]]
                    else: jsons[x][param["subSystem"] + f" {str(counter[param["subSystem"]] // 10)}"].append(param["name"])
                counter[param["subSystem"]] = counter[param["subSystem"]] + 1 if param["subSystem"] in counter.keys() else 1
            else: #if not put in general. those the same but in general
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
    """
    create the options for the current html file
    :return: list of the options.
    """
    ret = ""
    for sat in SATELLITES:
        ret += f"<option>{sat}</option>\n\t\t\t"
    return ret

def get_raw(raw, count):
    """make the raw data look more like hexDump."""
    return " ".join([raw[i - 2: i] if i % 16 != 0 else "".join(f"{raw[i - 2: i]}&nbsp&nbsp" if i % (16*count) != 0 else f"{raw[i - 2: i]}</br>") for i in range(2, len(raw), 2)] + [raw[len(raw) - 2:]])
  #  return raw

def make_for_html(sat_name, last_date, top, limit=0, width=1500):
    """
    take from SQL and put it in the format for the html. it's added to what I already have.
    :param width: the size of the windows when opened
    :param sat_name: name of sat as written in SATELLITES
    :param last_date: in time unix. say from where I need to take. (as time come) - type(str) but have int.
    :param top: is for the top of the page or for the bottom. according to that I know if I gave the min I have or the max
    :param limit: how many packet I take. if 0 take all.
    :return: build for html, min_date, max_date <- know what to take according to top or bottom.
    """
    #how many in a row.
    count_raw = math.ceil(width / 300) if width / 300 - math.floor(width) >= 0.8 else math.floor(width / 300) #get how to separate the raw
    limit = f"LIMIT {limit}" if limit != 0 else ""
    sat: dict = SATELLITES[sat_name] #get dict of the sat.
    sql_query = f"SELECT * FROM {sat['table_name']} WHERE {JSONS_FOR_HTML[sat['json']]['primaryKey']} {'>' if top else '<'} {last_date} ORDER BY {JSONS_FOR_HTML[sat['json']]['primaryKey']} DESC {limit}"
    with sat["threadLock"]: # when I can execute the query.
        sat["cursor"].execute(sql_query)
        data = sat["cursor"].fetchall()
    html_code = ""
    json_sorted = dict(sorted(JSONS_FOR_HTML[sat['json']].items())) #sort according to dictionary place
    time_params = json_sorted["time_param"] #what are the ones who need change to date.
    primary = json_sorted["primaryKey"] #who is the primaryKey (need only at the end)
    del json_sorted["primaryKey"], json_sorted["time_param"] #remove them so I will not look at that.
    count = count_raw if count_raw < len(json_sorted.keys()) else len(json_sorted.keys()) #get how to separate the subtypes
    width = 100 // count - 3 #count of % of subtype size
    for row in data: #go over each row that I got from the SQL (have 25 each time)
        #the start of the full part and the raw container
        html_code += f'<div class="containerPacket">\n<div class="divRaw">\n<div style="text-align: center"><u><b>Hex raw:</b></u></div>\n<div class="divHexRaw">{get_raw(row["raw"].upper(), count_raw)}</div></div>\n'
        already_did = 0
        for i in range(1, len(json_sorted) // count + 1): #going the len divided by count
            html_code += '<div class="container">\n'
            for k in range(count): #making the count small parts that are in a row (more will go down)
                html_code += f'<div class="containerSub" style="width:{width}%">\n<div class="titleSub">{list(json_sorted.keys())[already_did]}</div>\n<hr />\n'
                for param_name in json_sorted[list(json_sorted.keys())[already_did]]:
                    html_code += f'<u>{param_name}:</u> {row[param_name] if param_name not in time_params else datetime.fromtimestamp(row[param_name]).strftime("%d.%m.%Y %H:%M:%S")}<br />\n'
                html_code += '</div"></div>\n'
                already_did += 1
            html_code += '</div>\n'
        # if len is not divided by count, going at the end for the part that is left
        if len(json_sorted) % count != 0:
            html_code += '<div class="container">\n'
            for k in range(len(json_sorted) % count): #how much is left
                html_code += f'<div class="containerSub" style="width:{width}%">\n<div class="titleSub">{list(json_sorted.keys())[k + already_did]}</div>\n<hr />\n'
                for param_name in json_sorted[list(json_sorted.keys())[k + already_did]]:
                    html_code += f'<u>{param_name}:</u> {row[param_name] if param_name not in time_params else datetime.fromtimestamp(row[param_name]).strftime("%d.%m.%Y %H:%M:%S")}<br />\n'
                html_code += '</div"></div>\n'
            html_code += '</div>\n'
        html_code += '</div>\n'
    if not data: return "", last_date, last_date #if got nothing
    return html_code, data[-1][primary], data[0][primary] #else return

def make_excel(params):
    """
    make according to params and SQL an Excel table to send to client.
    :param params: dict that 100% have type and satName. all the other are according to type.
                    we can understand how to parse the request according to type.
    :return: excelTable, file_name
    """
    sql_filter = "" #because it doesn't have to be a where filter and there can be no filter at all.
    #get static for the function
    download_type = params["type"]
    json_format = SATELLITES[params["satName"]]["json"]
    primary_key = JSONS[json_format]["settings"]["prime_key"]
    if download_type == "StartToEndTime": #check between
        try: int(params["start"]) + int(params["end"])
        except Exception: raise TypeError("got something that is not int")
        sql_filter = f"WHERE {params["start"]} < {primary_key} AND {params["end"]} > {primary_key}"
    elif download_type == "StartTime": #get from startTime up to current
        try: int(params["start"])
        except Exception: raise TypeError("got something that is not int")
        sql_filter = f"WHERE {params["start"]} < {primary_key}"
    sql_query = f"SELECT * FROM {SATELLITES[params["satName"]]["table_name"]} {sql_filter} ORDER BY {primary_key} DESC " #make query
    if download_type == "Limit": #add limit if have
        try: int(params["limit"])
        except Exception: raise TypeError("got something that is not int")
        sql_query += f"LIMIT {params["limit"]}"
    with SATELLITES[params["satName"]]["threadLock"]:
        df = pd.read_sql(sql_query, connection_sql) #read the sql according to pandas
    for col in JSONS_FOR_HTML[json_format]["time_param"]: #chage format of unix_time to date-time format
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], unit='s')
            df[col] = df[col].dt.strftime('%d.%m.%Y %H:%M:%S')
    df["raw"] = df["raw"].str.upper() #big letters
    output = io.BytesIO() #temporary place
    file_name = f'{params["satName"]}_{datetime.now().strftime("%d-%m-%Y")}' #create file name
    with pd.ExcelWriter(output, engine='openpyxl') as writer: #make the writer with the .xslx engine
        df.to_excel(writer, index=False, sheet_name=file_name[:31]) #incase the file_name is bigger than possible, create excel
    return output, file_name

#satNogs, save to SQL
SIZE_IN_BYTES = {
    "uint": 4,
    "int": 4,
    "ushort": 2,
    "short": 2,
    "unixtime": 4, #will give integer.
    "float": 4,
    "byte": 1, #enum is TEXT, not enum is char(1)
    "string": 230, #need to check when we have the first 00, and according to that we know. that's the max written here.
    "double": 8
}

def doing_format(data, data_type, format_data):
    """
    change the params according to format or enum
    :param data: what are we doing the format on
    :param data_type: which type is this data
    :param format_data: the dict or string that we have there the format.
    :return: data after format.
    """
    # enum but I need string so that's how to make num a char of the num
    if data_type == "byte": return format_data[chr(ord(data) + 0x30)]
    # format we perfected before now only using it.
    if data_type in ["short", "ushort", "uint", "float", "double", "int"]:
        return eval(format_data, {"x": data})
    return data

def decoded_param(data_bytes, data_type, is_big):
    """
    with unpack take the hex and make it normal (readable).
    :param data_bytes: the data in hex
    :param data_type: which type
    :param is_big: is in big endian
    :return: data after changing from hex to data.
    """
    if data_type == "string": return data_bytes.decode("utf-8")
    if data_type == "byte": return unpack(('>' if is_big else '<') + "c", data_bytes)[0]
    if data_type == "short": return unpack(('>' if is_big else '<') + "h", data_bytes)[0]
    if data_type == "uint": return unpack(('>' if is_big else '<') + "I", data_bytes)[0]
    if data_type == "ushort": return unpack(('>' if is_big else '<') + "H", data_bytes)[0]
    if data_type == "float": return unpack(('>' if is_big else '<') + "f", data_bytes)[0]
    if data_type == "double": return unpack(('>' if is_big else '<') + "d", data_bytes)[0]
    if data_type in ["int", "unixtime"]: return unpack(('>' if is_big else '<') + "i", data_bytes)[0]

def decode_data_for_sql(data, json_params, setting):
    """
    getting parameters and by them making the params that needed to create the INSERT to the SQL.
    :param data: Hex that is only from the data section of Ax25
    :param json_params: according to what we will learn getting the params and the type of each.
    :param setting: have the setting of the json
    :return: values for SQL INSERT
    """
    i = setting["sizeof_header"] #where in the packet we start. (where the data is)
    decode_to_sql = []
    for param in json_params:
        if param["type"] != "string": #if not string, I know the size os take the data there
            bytes_from_data = data[i: i + SIZE_IN_BYTES[param["type"]]]
            i += SIZE_IN_BYTES[param["type"]]
        else: #try to find the first "\0" after to know where it ends.
            bytes_from_data = data[i: i + data[i:].index(0x00)]
            i += data[i:].index(0x00)
        if "isBigEndian" in param.keys():
            to_append = decoded_param(bytes_from_data, param["type"], param["isBigEndian"]) #if big send True or False
        else:
            to_append = decoded_param(bytes_from_data, param["type"], setting["isDefaultBigEndian"]) #send default
        if param["type"] == "byte" and "enum" in param.keys():
            to_append = doing_format(to_append, "byte", param["enum"]) #make the format of enum in byte, if we have
        elif "format" in param.keys():
            to_append = doing_format(to_append, param["type"], param["format"]) #format to all the other
        decode_to_sql.append(to_append) #add to the list of variables
    decode_to_sql.append(data.hex()) #also add raw
    return decode_to_sql

def check_respond(response):
    """
    get the response from the server and needed to check we don't have 429 error or invalid token.
    if invalid need to raise an error else need to wait and then continue.
    :param response: the response from the satNogs.
    :return: False or response.
    """
    if response.status_code == 404:  raise TypeError("Can't read from satNogs. Maybe they change url.")
    elif response.status_code == 401:
        if response.json()["detail"] == "Invalid token.":
            raise TypeError("Invalid Token to satNogs. Please change (explanation in doc)")
        else:
            raise TypeError("Non existing Token to satNogs. Please add (explanation in doc)")
    elif response.status_code == 429:
        print("read too much, wait a day and try again")
        time.sleep(24 * 60 * 60) #one day
        return False
    return response

class SatNogsToSQL:
    # IMPORTANT: satNogs doesn't like when we get too much in a day, so if it's not a new sat first get the csv and decrypt it.
    # have how below. (that mean also change the newestDates)
    def __init__(self, newest_dates=None):
        if not newest_dates: self.newest_dates = {SATELLITES[sat]["satnogs"]: "2000-01-01T00:00:00+00:00" for sat in SATELLITES}  #if didn't get put start.
        else:
            self.newest_dates = newest_dates
            for sat in SATELLITES:
                if SATELLITES[sat]["satnogs"] not in newest_dates:
                    self.newest_dates[SATELLITES[sat]["satnogs"]] = "2000-01-01T00:00:00+00:00"
        token = '935188971e64257d0736b4f89f575791312226fb'
        self.__headers = {'Authorization': f'Token {token}'}
        self.run = True
        self.__write_cursor = connection_sql.cursor()

    def check_packet(self, packet, timestamp):
        """
        get packet and check if it's time is bigger, have this callsign and the correct opcode.
        :param packet: one result of data (a full frame)
        :param timestamp: current timestamp of this packet
        :return: true, [sat name and frame (in bytes)] or False ["" or "time", ""]
        """
        frame = bytes.fromhex(packet)
        src = frame[:6] #place of callsign
        frame = frame[16:] #all the other packet (including our made headers)
        callsign = ''.join(chr(b >> 1) for b in src[:6]) # according to Ax25 protocol get callsign
        if callsign not in [SATELLITES[sat]["callsign"] for sat in SATELLITES]: return False, ["", ""] #if not in satellites
        #else get name, name in satnogs
        sat_name, satnog_name = [[sat, SATELLITES[sat]["satnogs"]] for sat in SATELLITES if callsign == SATELLITES[sat]["callsign"]][0]
        #check the time is fine, and we really need this packet, and it's not just because
        if datetime.fromisoformat(timestamp.replace("Z", "+00:00")) < datetime.fromisoformat(self.newest_dates[satnog_name]): return False, ["time", ""]
        #make sure we have the correct opcode
        opcode = bytes.fromhex(JSONS[SATELLITES[sat_name]["json"]]["settings"]["opcode"])
        place_opcode = JSONS[SATELLITES[sat_name]["json"]]["settings"]["place_start_opcode"] - 1
        if frame[place_opcode:place_opcode + len(opcode)] != opcode: return False, ["", ""]
        return True, [sat_name, frame]

    def enter_packets(self, packets):
        """
        enter packets (a full page) to sql
        :param packets: data in json from satNogs.
        :return: maxTime, if we had a problem.
        """
        results = packets["results"]
        ret_val = "fine"
        for res in results: #going over the packets
            ret = self.check_packet(res["frame"], res["timestamp"])
            if not ret[0]:  #if error
                if ret[1][0] != "time": continue
                else: # and time I need to stop.
                    ret_val = "time"
                    break
            sat_name, packet = ret[1] #get both satName and the frame (that is in bytes)
            json_file = JSONS[SATELLITES[sat_name]["json"]] #the dict of the json
            #get values to enter to SQL
            values = decode_data_for_sql(packet, json_file["subType"]["params"], json_file["settings"])
            #change to SQL insert values format.
            sql_query = f"INSERT OR IGNORE INTO {SATELLITES[sat_name]['table_name']} VALUES ({" ,".join([str(x) if type(x) != str else f"'{x}'" for x in values])});"
            self.__write_cursor.execute(sql_query)
        return str(datetime.fromisoformat(results[0]["timestamp"].replace("Z", "+00:00"))), ret_val  # need to add the check for the time. when I get there I should stop the loop and only do what's before. (by if == then)

    def infinite_loop(self):
        """
        loop of the reading for satNogs
        :return:nothing
        """
        try:
            while self.run:
                for norad_id in SatIds: #go through each sat that we have
                    url = f"https://db.satnogs.org/api/telemetry/?satellite={norad_id["noradId"]}"
                    try:
                        response = check_respond(requests.get(url, headers=self.__headers)) #ask for telemetry
                        while not response: response = check_respond(requests.get(url, headers=self.__headers))
                    except ConnectionError: raise TypeError("You aren't connect to the internet or something like that.")

                    data = response.json()
                    times, val = self.enter_packets(data) #get time and add to SQL
                    print("hi") #debug
                    if val == "time": #if time I want to exit
                        print("time") #debug
                        self.newest_dates[norad_id["satName"]] = times
                        connection_sql.commit()  # save it in SQL
                        time.sleep(120) #so the website we read from won't band as. that is true for all the sleep.
                        continue
                    time.sleep(20)
                    while data["next"]: #if we have another page
                        try:
                            response = check_respond(requests.get(data["next"], headers=self.__headers)) #get this one also
                            while not response: response = check_respond(requests.get(data["next"], headers=self.__headers))
                        except ConnectionError: raise TypeError("You aren't connect to the internet or something like that.")
                        data = response.json() #do the same as before
                        val = self.enter_packets(data)
                        if val[1] == "time":
                            print("time")
                            break
                        time.sleep(20)
                    self.newest_dates[norad_id["satName"]] = times
                    connection_sql.commit()  # save it in SQL
                    print("bye") #debug
                    time.sleep(120)
                time.sleep(7200) # 2 hours wait.
        finally:
            #at end write the most current.
            connection_sql.commit()
            with open("../jsons/newestTime.json", "w") as file: file.write(json.dumps(self.newest_dates))

    def setup(self):
        try:
            path = input("Enter path of csv to add (full path or relative): ")
            while path != "exit":
                date_start = "2000-01-01T00:00:00+00:00"
                sat_name = input("Enter satellite name according to satNOGS: ")
                with open(path, newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    count = 0
                    data = {"results": []}
                    for row in reader:
                        row = row[0]
                        if len(data["results"]) >= 25:
                            self.enter_packets(data)
                            data["results"] = []
                        data_mini = row.split("|")[:2]
                        data["results"].append(
                            {"timestamp": f"{data_mini[0].replace(" ", "T")}Z", "frame": data_mini[1]})
                        if not count:
                            date_start = f"{data_mini[0].replace(" ", "T")}+00:00"
                            count += 1
                self.newest_dates[sat_name] = date_start
                connection_sql.commit()
                path = input("Enter path of csv to add (full path or relative). \nexit to stop: ")
        finally:
            connection_sql.commit()
            with open("../jsons/newestTime.json", "w") as file:
                file.write(json.dumps(self.newest_dates))


def main():
    create_tables()
    with open("../jsons/newestTime.json", "r") as file:
        packets_to_sql = SatNogsToSQL(json.load(file))
    packets_to_sql.setup()

if __name__ == "__main__":
    try:
        main()
    finally: connection_sql.close()
