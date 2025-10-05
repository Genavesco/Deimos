import json

def extraer_datos_completos(spkid):
    nombre_archivo = f"PHA_detailed_{spkid}.json"
    
    try:
        with open(nombre_archivo, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Archivo {nombre_archivo} no encontrado.")
        return
    except json.JSONDecodeError:
        print(f"Error al leer el JSON en {nombre_archivo}.")
        return

    resultados = {}

    # --- VI DATA ---
    campos_impacto = ["date", "ps", "ts", "ip", "energy", "dist", "v_inf", "v_imp", "h", "diam", "mass"]
    vi_data = []
    for elemento in data.get("vi_data", []):
        fila = {campo: elemento.get(campo, None) for campo in campos_impacto}
        vi_data.append(fila)
    resultados["vi_data"] = vi_data

    # --- DISCOVERY ---
    campos_discovery = ["date", "location", "site"]
    discovery_data = {}
    discovery = data.get("discovery", {})
    for campo in campos_discovery:
        discovery_data[campo] = discovery.get(campo, None)
    resultados["discovery"] = discovery_data

    # --- ORBITAL ELEMENTS ---
    campos_orbital = ["e", "q", "w", "i", "a", "per", "per_y", "n"]
    orbital_data = {}
    elements = data.get("orbit", {}).get("elements", [])
    for elemento in elements:
        nombre = elemento.get("name")
        valor = elemento.get("value")
        if nombre in campos_orbital:
            orbital_data[nombre] = valor
    resultados["orbital"] = orbital_data

    return resultados

# --- EJEMPLO DE USO ---
spkid = input("Ingrese el SPKID: ")
datos = extraer_datos_completos(spkid)

if datos:
    print("\n--- VI DATA ---")
    for i, d in enumerate(datos["vi_data"], start=1):
        print(f"\nElemento {i}:")
        for k, v in d.items():
            print(f"{k}: {v}")

    print("\n--- DISCOVERY ---")
    for k, v in datos["discovery"].items():
        print(f"{k}: {v}")

    print("\n--- ORBITAL ELEMENTS ---")
    for k, v in datos["orbital"].items():
        print(f"{k}: {v}")
