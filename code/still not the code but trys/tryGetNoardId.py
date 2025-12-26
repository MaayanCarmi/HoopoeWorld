import requests



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


# Example: Search for a weather satellite
print(get_satnogs_info("NOAA 19"))