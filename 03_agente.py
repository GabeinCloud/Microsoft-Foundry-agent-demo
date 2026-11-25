"""Phase 3: define a Prompt Agent in Python and connect File Search."""

from hashlib import sha256

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchTool, PromptAgentDefinition
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential

from comun import cargar_estado, configuracion, ejecutar, exigir_documento, guardar_estado

INSTRUCCIONES = """You are a business assistant specialized in answering questions about internal documents.

Use File Search to retrieve relevant information.

Answer only with information grounded in the document.

If you cannot find the answer, say that the information is not available.

Answer clearly and concisely, in the same language as the user's question.

Include references to the document whenever they are available."""

# Sample chat questions:
# How many vacation days do I get per year?
# Can I work from home two days a week?


def main():
    endpoint, modelo, nombre = configuracion()
    estado = cargar_estado(endpoint)
    almacen_id = exigir_documento(estado)

    # The definition runs in Foundry; everything is configured by this code.
    definicion = PromptAgentDefinition(
        model=modelo,
        instructions=INSTRUCCIONES,
        tools=[FileSearchTool(vector_store_ids=[almacen_id])],
        tool_choice="required",
    )
    huella = sha256(str(definicion.as_dict()).encode("utf-8")).hexdigest()

    with (
        DefaultAzureCredential() as credencial,
        AIProjectClient(endpoint=endpoint, credential=credencial) as proyecto,
        proyecto.get_openai_client() as cliente,
    ):
        almacen = cliente.vector_stores.retrieve(almacen_id)
        if almacen.status != "completed":
            raise ValueError("The Vector Store is not ready yet. Run 02_documento.py.")

        # Looking for the same configuration avoids a new version on every run.
        try:
            agente = next((
                version for version in proyecto.agents.list_versions(agent_name=nombre)
                if (version.metadata or {}).get("demo_config") == huella
            ), None)
        except ResourceNotFoundError:
            agente = None
        if agente is None:
            agente = proyecto.agents.create_version(
                agent_name=nombre,
                definition=definicion,
                metadata={"demo_config": huella},
                description="Introductory demo: questions about the company handbook.",
            )
            print("Created a new agent version.")
        else:
            print("Reusing an existing version.")
        estado.update(agent_name=agente.name, agent_version=agente.version, model=modelo)
        guardar_estado(estado)
        print(f"Agent: {agente.name}\nVersion: {agente.version}\nModel: {modelo}")


if __name__ == "__main__":
    ejecutar(main)

