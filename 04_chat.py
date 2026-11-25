"""Phase 4: chat with the existing agent, without creating another agent."""

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from comun import cargar_estado, configuracion, ejecutar, exigir_documento


COMANDOS_SALIDA = ("exit", "salir", "sair")


def mostrar_respuesta(respuesta):
    print(f"\nAgent: {respuesta.output_text}")
    referencias = set()
    # References live in the message annotations, not only in output_text.
    for salida in respuesta.output:
        if salida.type != "message":
            continue
        for contenido in salida.content:
            if contenido.type == "output_text":
                for anotacion in contenido.annotations:
                    if anotacion.type == "file_citation":
                        nombre = getattr(anotacion, "filename", None) or "Document"
                        referencias.add(f"{nombre} ({anotacion.file_id})")
    for referencia in sorted(referencias):
        print(f"Source: {referencia}")
    print()


def main():
    endpoint, modelo, nombre = configuracion()
    estado = cargar_estado(endpoint)
    exigir_documento(estado)
    if not estado.get("agent_version") or estado.get("agent_name") != nombre:
        raise ValueError("Run 03_agente.py first for this agent.")
    if estado.get("model") != modelo:
        raise ValueError("The deployment has changed. Run 03_agente.py before the chat.")

    with (
        DefaultAzureCredential() as credencial,
        AIProjectClient(endpoint=endpoint, credential=credencial) as proyecto,
        proyecto.get_openai_client() as cliente,
    ):
        agente = proyecto.agents.get_version(
            agent_name=nombre, agent_version=estado["agent_version"],
        )
        # Foundry keeps the history of this conversation between questions.
        conversacion = cliente.conversations.create()
        print(f"{agente.name} | version {agente.version}")
        print(f"Conversation: {conversacion.id}\nType a question or 'exit'.")
        while True:
            pregunta = input("You: ").strip()
            if pregunta.casefold() in COMANDOS_SALIDA:
                break
            if not pregunta:
                continue
            respuesta = cliente.responses.create(
                conversation=conversacion.id,
                input=pregunta,
                extra_body={"agent_reference": {
                    "name": agente.name,
                    "version": agente.version,
                    "type": "agent_reference",
                }},
            )
            if respuesta.status != "completed":
                raise ValueError(f"Incomplete response: {respuesta.status}. Try again.")
            mostrar_respuesta(respuesta)
        print("Conversation finished. No resources were deleted.")


if __name__ == "__main__":
    ejecutar(main)

    # Sample chat questions:
    # How many vacation days do I get per year?
    # Can I work from home two days a week?
    # I'm going on a business trip; what are the expense policies?