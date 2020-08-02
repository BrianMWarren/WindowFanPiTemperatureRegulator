import requests

#send dweet.io and update on temperature status
dweetContent = {
    "TestTemp": 99
}
dweet = {
  "thing": "409HouseWeather",
  "key": "Bni05-8BtiA-8FV8z-1h0$9-9IGtI-8k1qo-A6XuO-EC2O2-1t@BZ-FfJbn-1MweA-6mssX-4ib4s-wab-1W",
  "content": dweetContent
}
header = {"X-Dweet-Auth": "eyJyb2xlIjoiYXV0byIsImNvbXBhbnkiOiJTVVBFUlNQRUNJQUxOT05FTk9USElOR05PVEFOT1JHSU5JWkFUSU9OIiwiZ2VuZXJhdGVkIjoxNTk0NjgxNTI4MjQzfQ==.f52b975dd0a588a2b4ff59633d64ec5189f811e814bdc79d59fc66c53acc27e9"}
URL = "https://dweetpro.io:443/v2/dweets"
r = requests.post(url = URL, headers = header, json = dweet)
print(r)