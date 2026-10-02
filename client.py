import requests

data = {
    "asset_id": 1,
    "voltage": 433,
    "current": 520,
    "temperature": 68,
    "load": 350
}

# Send measurement
response = requests.post(
    "http://127.0.0.1:8000/measurements",
    json=data
)

print("Measurement:")
print(response.json())

# Get updated asset status
status_response = requests.get(
    "http://127.0.0.1:8000/assets/1/status"
)

print("\nAsset Status:")
print(status_response.json())