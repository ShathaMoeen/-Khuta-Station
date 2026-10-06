import requests

BASE = "http://127.0.0.1:8000"

r = requests.post(f"{BASE}/visitors", json={"lang": "en", "level": "beginner", "consent": True})
print("تسجيل:", r.status_code, r.json())
card = r.json()["card_id"]

r = requests.post(f"{BASE}/taps", json={"card_id": card, "station_code": "ST-01"})
print("تمرير:", r.status_code, r.json())
iid = r.json()["interaction_id"]

r = requests.post(f"{BASE}/interactions/{iid}/duration", json={"duration_s": 45})
print("مدة:", r.status_code, r.json())

r = requests.get(f"{BASE}/visitors/{card}/summary")
print("ملخص:", r.status_code, r.json())

r = requests.post(f"{BASE}/visitors", json={"lang": "tr", "level": "beginner", "consent": True})
card2 = r.json()["card_id"]
r = requests.post(f"{BASE}/taps", json={"card_id": card2, "station_code": "ST-01"})
print("احتياط اللغة:", r.status_code, r.json()["content"]["lang"], "fallback =", r.json()["content"]["fallback"])