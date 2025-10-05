import os
import re
import requests
import numpy as np
import pandas as pd
from urllib.parse import quote
import plotly.graph_objects as go
from dash import Dash, html, dcc, Output, Input

# -----------------------------
# Configuración inicial
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_ABSOLUTA = os.path.join(BASE_DIR, "cneos_sentry_summary_data.csv")
HEAD_LIMIT = 1994
EMERGENCY_LIST = ["433 Eros", "99942 Apophis"]

# -----------------------------
# Leer CSV o usar lista de respaldo
# -----------------------------
try:
    df = pd.read_csv(CSV_ABSOLUTA)
    df.columns = [c.strip() for c in df.columns]
    posibles = [col for col in df.columns if any(token in col.lower() for token in ["design", "object", "name", "des"])]
    COLUMN_NAME = posibles[0] if posibles else df.columns[0]
    ASTEROIDES_PARA_MENU = df[COLUMN_NAME].dropna().astype(str).str.strip().head(HEAD_LIMIT).tolist()
    if not ASTEROIDES_PARA_MENU:
        ASTEROIDES_PARA_MENU = EMERGENCY_LIST
except Exception:
    ASTEROIDES_PARA_MENU = EMERGENCY_LIST

# Limpieza de nombres
def limpiar_nombre(nombre):
    nombre = re.sub(r"^\d+\s*", "", nombre)
    return nombre.replace("(", "").replace(")", "").strip()

ASTEROIDES_PARA_MENU = [limpiar_nombre(n) for n in ASTEROIDES_PARA_MENU]

# -----------------------------
# Función para obtener elementos orbitales desde la API
# -----------------------------
def fetch_orbit_elements(asteroide_name):
    url = f"https://ssd-api.jpl.nasa.gov/sbdb.api?des={quote(asteroide_name)}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
    except Exception:
        return None

    orbit = data.get("orbit")
    if not orbit:
        return None

    if isinstance(orbit, dict) and "elements" in orbit and isinstance(orbit["elements"], list):
        try:
            return {elem["name"]: elem["value"] for elem in orbit["elements"]}
        except Exception:
            return None

    if isinstance(orbit, dict):
        simple = {}
        for k, v in orbit.items():
            try:
                simple[str(k)] = v
            except Exception:
                pass
        if 'a' in simple and 'e' in simple:
            return simple

    return None

# -----------------------------
# Función para crear órbita 3D
# -----------------------------
def create_orbit(a, e, i, omega, w, color, name):
    theta = np.linspace(0, 2*np.pi, 500)
    b = a * np.sqrt(1 - e**2)
    x = a * np.cos(theta) - e
    y = b * np.sin(theta)
    z = np.zeros_like(theta)

    def rotation_matrix(omega, i, w):
        Rz_omega = np.array([
            [np.cos(omega), -np.sin(omega), 0],
            [np.sin(omega),  np.cos(omega), 0],
            [0, 0, 1]
        ])
        Rx_i = np.array([
            [1, 0, 0],
            [0, np.cos(i), -np.sin(i)],
            [0, np.sin(i),  np.cos(i)]
        ])
        Rz_w = np.array([
            [np.cos(w), -np.sin(w), 0],
            [np.sin(w),  np.cos(w), 0],
            [0, 0, 1]
        ])
        return Rz_omega @ Rx_i @ Rz_w

    R = rotation_matrix(omega, i, w)
    coords = R @ np.vstack((x, y, z))

    return go.Scatter3d(
        x=coords[0], y=coords[1], z=coords[2],
        mode='lines',
        line=dict(color=color, width=3),
        name=name
    )

# -----------------------------
# Figura base (Sol + Tierra)
# -----------------------------
def create_base_figure():
    fig = go.Figure()

    # Sol
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode='markers+text',
        text=["Sol"],
        textposition="top center",
        marker=dict(size=10, color='yellow'),
        textfont=dict(color='white'),
        name='Sol'
    ))

    # Órbita Tierra
    fig.add_trace(create_orbit(
        a=1.000, e=0.0167, i=np.radians(0.0),
        omega=np.radians(0.0), w=np.radians(102.9),
        color='blue', name="Órbita Tierra"
    ))

    # Órbita marte
    fig.add_trace(create_orbit(
        a=1.523679, e=0.093315, i=np.radians(1.850),
        omega=np.radians(49.562), w=np.radians(286.537),
        color='red', name="Órbita marte"
    ))

    # Tierra
    fig.add_trace(go.Scatter3d(
        x=[1], y=[0], z=[0],
        mode='markers+text',
        text=["Tierra"],
        textposition="top center",
        marker=dict(size=8, color='green'),
        textfont=dict(color='white'),
        name='Tierra'
    ))

    # Mercurio
    fig.add_trace(go.Scatter3d(
        x=[0.307003604], y=[-0.285432466], z=[-0.047202202],
        mode='markers+text',
        text=["Mercurio"],
        textposition="top center",
        marker=dict(size=8, color='violet'),
        textfont=dict(color='white'),
        name='Mercurio'
    ))

    # Órbita mercurio
    fig.add_trace(create_orbit(
        a=0.387098, e=0.205630, i=np.radians(7.004),
        omega=np.radians(29.124), w=np.radians(48.331),
        color='violet', name="Órbita Mercurio"
    ))

    # Órbita venus
    fig.add_trace(create_orbit(
        a=0.7233, e=0.0068, i=np.radians(3.39),
        omega=np.radians(55.19), w=np.radians(76.68),
        color='pink', name="Órbita Venus"
    ))

    # Venus
    fig.add_trace(go.Scatter3d(
        x=[0.41217827], y=[0.592826], z=[0.002770281],
        mode='markers+text',
        text=["Venus"],
        textposition="top center",
        marker=dict(size=8, color='pink'),
        textfont=dict(color='white'),
        name='Venus'
    ))

    # marte
    fig.add_trace(go.Scatter3d(
        x=[0.433465502], y=[1.459892395], z=[0.0191889],
        mode='markers+text',
        text=["marte"],
        textposition="top center",
        marker=dict(size=8, color='orange'),
        textfont=dict(color='white'),
        name='marte'
    ))

    fig.update_layout(
        scene=dict(
            xaxis_title='X (UA)',
            yaxis_title='Y (UA)',
            zaxis_title='Z (UA)',
            aspectmode="data",
            xaxis=dict(backgroundcolor="black", color="white", gridcolor="gray"),
            yaxis=dict(backgroundcolor="black", color="white", gridcolor="gray"),
            zaxis=dict(backgroundcolor="black", color="white", gridcolor="gray")
        ),
        paper_bgcolor='black',
        plot_bgcolor='black',
        title=dict(text="Órbita 3D del Sistema Solar Interior", font=dict(color='white')),
        legend=dict(font=dict(color='white'))
    )

    return fig

# -----------------------------
# Crear app Dash
# -----------------------------
app = Dash(__name__)
app.title = "Simulador de Órbitas de Asteroides"

app.layout = html.Div(
    style={"backgroundColor": "black", "color": "white", "textAlign": "center", "padding": "20px"},
    children=[
        html.H2("🪐 Simulador de Órbitas de Asteroides (NASA SBDB API)"),
        html.Label("Selecciona un asteroide:"),
        dcc.Dropdown(
            id="asteroide-dropdown",
            options=[{"label": n, "value": n} for n in ASTEROIDES_PARA_MENU],
            placeholder="Elige un asteroide...",
            style={"width": "50%", "margin": "auto", "color": "black"}
        ),
        html.Div(id="status-text", style={"marginTop": "15px"}),
        dcc.Graph(id="orbit-graph", figure=create_base_figure(), style={"height": "90vh"})
    ]
)

# -----------------------------
# Callback interactivo
# -----------------------------
@app.callback(
    [Output("orbit-graph", "figure"), Output("status-text", "children")],
    [Input("asteroide-dropdown", "value")]
)
def actualizar_orbita(asteroide_name):
    fig = create_base_figure()

    if not asteroide_name:
        return fig, "🌍 Selecciona un asteroide para mostrar su órbita."

    status = f"⏳ Descargando elementos orbitales de {asteroide_name}..."
    elems = fetch_orbit_elements(asteroide_name)
    if not elems:
        return fig, f"No se pudieron obtener datos para {asteroide_name}."

    try:
        a = float(elems.get("a") or elems.get("A"))
        e = float(elems.get("e") or elems.get("E"))
        i_deg = float(elems.get("i") or elems.get("I"))
        om_deg = float(elems.get("om") or elems.get("node") or elems.get("OM") or elems.get("Om"))
        w_deg = float(elems.get("w") or elems.get("argp") or elems.get("pericenter") or elems.get("W"))
    except Exception:
        return fig, f"Datos incompletos para {asteroide_name}."

    fig.add_trace(create_orbit(
        a=a, e=e,
        i=np.radians(i_deg),
        omega=np.radians(om_deg),
        w=np.radians(w_deg),
        color="cyan", name=asteroide_name
    ))

    fig.update_layout(title=f"Órbita 3D de {asteroide_name} junto a la Tierra")
    status = f" Órbita de {asteroide_name} cargada correctamente."

    return fig, status

# -----------------------------
# Ejecutar servidor
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)