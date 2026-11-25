"""Local configuration, state and errors; contains no agent logic."""

import json
import os
from pathlib import Path

from azure.core.exceptions import AzureError
from dotenv import load_dotenv
from openai import OpenAIError

RAIZ = Path(__file__).resolve().parent
ESTADO = RAIZ / "estado.json"


def configuracion():
    load_dotenv(RAIZ / ".env")
    endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "").strip().rstrip("/")
    modelo = os.getenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "").strip()
    nombre = os.getenv("AGENT_NAME", "DocumentAssistant").strip()
    if not endpoint or not modelo or not nombre:
        raise ValueError("Fill in the endpoint, the deployment and the agent name in .env.")
    if not endpoint.startswith("https://") or "/api/projects/" not in endpoint:
        raise ValueError("Use the Foundry project endpoint, with /api/projects/PROJECT.")
    if modelo == "YOUR_DEPLOYMENT_NAME" or "YOUR_RESOURCE" in endpoint:
        raise ValueError("Replace the .env placeholders with the values of your project.")
    return endpoint, modelo, nombre


def cargar_estado(endpoint):
    if not ESTADO.exists():
        return {"project_endpoint": endpoint}
    estado = json.loads(ESTADO.read_text(encoding="utf-8"))
    if not isinstance(estado, dict) or estado.get("project_endpoint") != endpoint:
        raise ValueError("estado.json belongs to another project or is not valid. No resources will be created.")
    return estado


def guardar_estado(estado):
    # Atomic replacement keeps the IDs even if a phase is interrupted.
    temporal = ESTADO.with_suffix(".tmp")
    temporal.write_text(json.dumps(estado, indent=2, ensure_ascii=False), encoding="utf-8")
    temporal.replace(ESTADO)


def exigir_documento(estado):
    if not estado.get("vector_store_id") or not estado.get("documento_listo"):
        raise ValueError("Run 02_documento.py first and wait until indexing finishes.")
    return estado["vector_store_id"]


def ejecutar(funcion):
    try:
        funcion()
    except (KeyboardInterrupt, EOFError):
        print("\nDone. No Azure resources were deleted.")
    except (AzureError, OpenAIError, OSError, ValueError) as error:
        codigo = getattr(error, "status_code", None)
        print(f"Error: {error}")
        if codigo == 401:
            print("Check your Microsoft Entra ID sign-in and the project tenant.")
        elif codigo == 403:
            print("Check the Foundry User role (formerly Azure AI User) on the project.")
        elif codigo == 404:
            print("Check the endpoint, the deployment and the IDs in estado.json. Do not delete the state to retry.")
        elif codigo == 429:
            print("Quota or rate limit reached. Wait and try again.")
        raise SystemExit(1) from None