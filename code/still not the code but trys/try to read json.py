__author__ = 'Maayan'

import sqlite3
import json

# need to try to make the reader form the sqlite3. like I think I will need each time to check what is what and keep it.

def main():
    # params = {
    #
    # }
    # with open(r"..\..\jsons\tevels_beacon.json", 'r') as file:
    #     data = json.load(file)
    # data = data["subType"]["params"]
    # for param in data:  # maybe check if there is a way we will write in little endian
    #     if "subSystem" in param.keys():
    #         if param["subSystem"] in params.keys(): params[param["subSystem"]] += f'<br/>\n{param["name"]}: '
    #         else: params[param["subSystem"]] = f'{param["name"]}: '
    #     else:
    #         if "General" in params.keys(): params["General"] += f'<br/>\n{param["name"]}: '
    #         else: params[param["General"]] = f'{param["name"]}: '
    # for key in params.keys():
    #     print(f"{key}:\n{params[key]}\n\n")
    """other stuff that maybe useful"""
#     s = """voltBattery: 7882<br />
# volt_5V: 4992<br />
# volt_3V3: 3320<br />
# charging_power: -130<br />
# consumed_power: 3430<br />
# electric_current: -29<br />
# current_3V3: 125<br />
# current_5V: 0<br />
# bat_temp: 10<br />
# eps_state: 0
# """
#     l = s.split("\n")
#     for i in l:
#         print(" ".join([f'<u>{i.split(" ")[0]}</u>', " ".join(i.split(" ")[1:])]))
    pass
if __name__ == "__main__":
    main()
