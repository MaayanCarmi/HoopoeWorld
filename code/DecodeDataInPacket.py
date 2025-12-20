__author__ = 'Maayan'
import json
from struct import unpack
from datetime import datetime

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
    if data_type == "unixtime":
        return datetime.fromtimestamp(data).strftime("%d.%m.%Y %H:%M:%S")

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
        elif param["type"] == "unixtime":
            to_append = doing_format(to_append, "unixtime", None)
        elif "format" in param.keys():
            to_append = doing_format(to_append, param["type"], param["format"])
        decode_to_sql.append(to_append)
    decode_to_sql.append(data)
    return decode_to_sql

def main():
    #check it.
    with open(r'..\jsons\tevels_beacon.json', 'r') as file:
        data = json.load(file)
    dec = decode_data_for_sql("0000000B00018D00CA1E8013F80C7EFF660DE3FF7D0000000A00000ABD410050384100DC664100611A42007EBA410004474135F02F6900C01B470000000000A0F17700E0D530000000001200000074CF0F0000000000FFFFFFFFFFFFFFFF2BCEC822D9E483220400000000CA3640601D20690000FFFFFFFF000B00000050613A425671F941F7B17E4051F82444B2BADDC50000DDC2",data["subType"]["params"], False)

    print(dec)

if __name__ == "__main__":
    main()
