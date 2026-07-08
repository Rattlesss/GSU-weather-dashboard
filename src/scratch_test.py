import requests

url = "https://power.larc.nasa.gov/api/temporal/daily/point"
params = {
    "parameters": "T2M,PRECTOTCORR",
    "community": "RE",
    "longitude": -81.7767,
    "latitude": 32.4194,
    "start": "20250101",
    "end": "20251231",
    "format": "JSON"
}

response = requests.get(url, params=params)
print(response.status_code)
print(response.json())
