import pandas as pd
import requests
import os
import re
from datetime import datetime
from utils import get_resource_path

# Ruta al Excel con los RUCs
DB_PATH = os.path.join(os.getcwd(), "db", "DB-CONSULTA.xlsx")

# Directorio público para los archivos de salida
OUTPUT_DIR = os.path.join(os.getcwd(), "static", "consultas")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# URL de la API
API_URL = "https://consultaweb.ant.gob.ec/PortalWEB/paginas/clientes/clp_json_citaciones.jsp"

def consultar_api(ruc):
    ruc = str(ruc).zfill(13)

    params = {
        "ps_opcion": "P",
        "ps_id_contrato": "",
        "ps_id_persona": "19664470",
        "ps_placa": "",
        "ps_identificacion": ruc,
        "ps_tipo_identificacion": "RUC",
        "_search": "false",
        "nd": "1740414553893",
        "rows": "50",
        "page": "1",
        "sidx": "fecha_emision",
        "sord": "desc"
    }

    try:
        response = requests.get(API_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if "rows" in data and isinstance(data["rows"], list) and data["records"] > 0:
            return data["rows"]
        else:
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error al consultar {ruc}: {e}")
        return None

def consultar_ruc():
    df = pd.read_excel(DB_PATH, sheet_name="RUC", dtype=str)
    data_list = []

    for ruc in df["RUC"]:
        resultado = consultar_api(ruc)
        if resultado:
            for row in resultado:
                row_data = [ruc] + row["cell"]
                data_list.append(row_data)

    if data_list:
        column_names = ["RUC", "N. Citación", "# Infracción", "Entidad", "# Citación", "Placa", "Doc.",
                       "Fecha de emisión", "Fecha de notificación", "Limite de Pago", "Puntaje", "Col_L", "Col_M",
                       "Col_N", "Sanción", "Multa", "Remisión", "Total a pagar", "Artículo/Literal", "Col_T", "Col_U"]

        df_resultado = pd.DataFrame(data_list, columns=column_names[:len(data_list[0])], dtype=str)
        df_resultado = df_resultado.loc[:, ~df_resultado.columns.str.match(r'^Col_[A-Z]$')]

        fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"RUC-CON-{fecha_actual}.xlsx"
        output_path = os.path.join(OUTPUT_DIR, filename)
        df_resultado.to_excel(output_path, index=False)

        # URL pública del archivo generado
        download_url = f"/static/consultas/{filename}"

        return {"success": True, "download_url": download_url, "message": "Consulta completada con éxito."}
    else:
        return {"success": False, "message": "No se encontraron RUCs con multas."}
