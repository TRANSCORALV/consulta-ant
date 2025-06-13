import pandas as pd
import requests
import os
import re
from datetime import datetime

# Ruta del archivo Excel
DB_PATH = os.path.join(os.getcwd(), "db", "DB-CONSULTA.xlsx")

# Carpeta de salida accesible públicamente
OUTPUT_DIR = os.path.join(os.getcwd(), "static", "consultas")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# URLs de la API
ID_PERSONA_URL = "https://consultaweb.ant.gob.ec/PortalWEB/paginas/clientes/clp_json_consulta_persona.jsp"
CITACIONES_URL = "https://consultaweb.ant.gob.ec/PortalWEB/paginas/clientes/clp_json_citaciones.jsp"

def obtener_id_persona(cedula):
    params = {
        "ps_tipo_identificacion": "CED",
        "ps_identificacion": cedula
    }
    
    try:
        response = requests.get(ID_PERSONA_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        return data.get("id_persona")
    
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener id_persona para {cedula}: {e}")
        return None

def consultar_api(cedula, id_persona):
    cedula = str(cedula).zfill(10)

    params = {
        "ps_opcion": "P",
        "ps_id_contrato": "",
        "ps_id_persona": id_persona,
        "ps_placa": "",
        "ps_identificacion": cedula,
        "ps_tipo_identificacion": "CED",
        "_search": "false",
        "nd": "1740430241436",
        "rows": "50",
        "page": "1",
        "sidx": "fecha_emision",
        "sord": "desc"
    }

    try:
        response = requests.get(CITACIONES_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if "rows" in data and isinstance(data["rows"], list) and data["records"] > 0:
            return data["rows"]
        else:
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error al consultar {cedula}: {e}")
        return None

def consultar_cedula_in():
    df = pd.read_excel(DB_PATH, sheet_name="CEDULA-IN", dtype=str)
    data_list = []

    for cedula in df["CEDULA"]:
        cedula_str = str(cedula).zfill(10)
        id_persona = obtener_id_persona(cedula_str)

        if id_persona:
            print(f"Consultando cédula {cedula_str} con id_persona {id_persona}")
            resultado = consultar_api(cedula_str, id_persona)
            if resultado:
                for row in resultado:
                    row_data = [cedula_str] + row["cell"]
                    data_list.append(row_data)
        else:
            print(f"No se pudo obtener id_persona para la cédula {cedula_str}")

    if data_list:
        column_names = ["Cedula", "N. Citación", "# Infracción", "Entidad", "# Citación", "Placa", "Doc.",
                        "Fecha de emisión", "Fecha de notificación", "Limite de Pago", "Puntaje", "Col_L", "Col_M",
                        "Col_N", "Sanción", "Multa", "Remisión", "Total a pagar", "Artículo/Literal", "Col_T", "Col_U"]

        df_resultado = pd.DataFrame(data_list, columns=column_names[:len(data_list[0])], dtype=str)
        df_resultado = df_resultado.loc[:, ~df_resultado.columns.str.match(r'^Col_[A-Z]$')]

        fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"in-ced-con-{fecha_actual}.xlsx"
        output_path = os.path.join(OUTPUT_DIR, filename)
        df_resultado.to_excel(output_path, index=False)

        download_url = f"/static/consultas/{filename}"

        return {"success": True, "download_url": download_url, "message": "Consulta completada con éxito."}
    else:
        return {"success": False, "message": "No se encontraron cédulas con multas."}

if __name__ == "__main__":
    resultado = consultar_cedula_in()
    print(resultado["message"])
