import requests
from datetime import datetime

token = '7fb141fe2017233114f1539a24ab64bb49850a91'

newest_date = {

}

def get_satnogs_info(search_query):
    # This searches the SatNOGS database for a look a like name
    url = f"https://db.satnogs.org/api/satellites/?search&format=json"

    try:
        response = requests.get(url)
        data = response.json()
        count = 0
        if not data:
            return "No satellite found with that name."
        for sat in data:
            print({
            "Name": sat['name'],
            "NORAD ID": sat['norad_cat_id'],
            "Status": sat['status'],
        })
            count += 1
        print(count)
        # We'll grab the first result
        sat = data[0]
        return {
            "Name": sat['name'],
            "NORAD ID": sat['norad_cat_id'],
            "Status": sat['status'],
        }
    except Exception as e:
        return f"Error connecting to SatNOGS: {e}"


def telem():
    url = f"https://network.satnogs.org/api/observations/?sat_id=TJDQ-0178-9438-9402-8155&results=d1"
    headers = {'Authorization': f'Token {token}'}

    response = requests.get(url, headers=headers)
    data = response.json()
    print(data)

# for item in telem():
#     print({"timestamp": item["timestamp"], "frame": item["frame"]})

#telem()
# frame = bytes.fromhex("A8AC98645A68E0A8AC98645A686303F0")
#
# src = frame[:7]
# frame = frame[16:]
# callsign = ''.join(chr(b >> 1) for b in src[:6])
#
# print(f"{callsign} : {frame}")
x = datetime.fromisoformat("2025-12-28T03:38:02Z".replace("Z", "+00:00"))
print(str(x))