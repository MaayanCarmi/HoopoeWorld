import requests

token = '935188971e64257d0736b4f89f575791312226fb'


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
    url = f"https://db.satnogs.org/api/telemetry/?satellite=63213"
    headers = {'Authorization': f'Token {token}'}

    response = requests.get(url, headers=headers)
    data = response.json()
    return data

for item in telem():
    print(item)
fram = {"hello": 1}
