"""Phase 1: a question to a model, still without an agent or documents."""

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from comun import configuracion, ejecutar


def main():
    endpoint, modelo, _ = configuracion()

    # Entra ID provides the token; no API key is needed.
    with (
        DefaultAzureCredential() as credencial,
        AIProjectClient(endpoint=endpoint, credential=credencial) as proyecto,
        proyecto.get_openai_client() as cliente,
    ):
        respuesta = cliente.responses.create(
            model=modelo,
            input="Explain in two sentences, in English, what a language model is.",
        )
        if respuesta.status != "completed":
            raise ValueError(f"The response did not complete correctly: {respuesta.status}")
        print(respuesta.output_text)


if __name__ == "__main__":
    ejecutar(main)