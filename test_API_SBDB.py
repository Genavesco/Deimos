import requests
import json

def get_potentially_hazardous_asteroids():
    url = (
        "https://ssd-api.jpl.nasa.gov/sbdb_query.api?"
        "fields=full_name,spkid,a,e,q,i,w,per,per_y,n,H,diameter,GM,density,albedo"
        "&sb-group=pha"
    )

    print("🚀 Consultando JPL SBDB: PHAs...")
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"HTTP Error {response.status_code}: {response.text}")

    data = response.json()
    if "data" not in data or not data["data"]:
        raise Exception(f"Respuesta inesperada o vacía: {data}")

    fields = data["fields"]
    phas = [dict(zip(fields, row)) for row in data["data"]]

    print(f"✅ Se encontraron {len(phas)} PHAs.")
    with open("PHA_data.json", "w", encoding="utf-8") as f:
        json.dump(phas, f, indent=4, ensure_ascii=False)
    print("💾 Datos guardados en PHA_data.json")

    return phas

def get_detailed_asteroid_data(spkid):
    url = f"https://ssd-api.jpl.nasa.gov/sbdb.api?spk={spkid}&phys-par=1&vi-data=1&discovery=1"
    print(f"🔍 Consultando datos detallados del asteroide SPKID={spkid}...")
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"HTTP Error {response.status_code}: {response.text}")

    data = response.json()
    with open(f"PHA_detailed_{spkid}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"💾 Datos detallados guardados en PHA_detailed_{spkid}.json")
    return data

if __name__ == "__main__":
    phas = get_potentially_hazardous_asteroids()

    # Ejemplo: elegimos el primero de la lista
    elegido = phas[55]["spkid"]
    detalle = get_detailed_asteroid_data(elegido)
