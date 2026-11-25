"""Phase 2: index the PDF and recover deleted resources to repeat the demo."""

from hashlib import sha256

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from openai import NotFoundError

from comun import RAIZ, cargar_estado, configuracion, ejecutar, guardar_estado


def main():
    endpoint, _, _ = configuracion()
    documento = RAIZ / "documentos" / "manual_empresa.pdf"
    huella = sha256(documento.read_bytes()).hexdigest()
    estado = cargar_estado(endpoint)
    if estado.get("pdf_sha256") not in (None, huella):
        raise ValueError("The PDF has changed. Restore the original or prepare another demo; the upload will not be duplicated.")

    with (
        DefaultAzureCredential() as credencial,
        AIProjectClient(endpoint=endpoint, credential=credencial) as proyecto,
        proyecto.get_openai_client() as cliente,
    ):
        if estado.get("vector_store_id"):
            try:
                cliente.vector_stores.retrieve(estado["vector_store_id"])
            except NotFoundError:
                print("The Vector Store was deleted in Foundry. A new one will be created for the demo.")
                estado.update(vector_store_id=None, file_id=None, documento_listo=False)
                estado.pop("agent_version", None)
                guardar_estado(estado)
        if not estado.get("vector_store_id"):
            almacen = cliente.vector_stores.create(name="ManualEmpresaDemo")
            estado.update(vector_store_id=almacen.id, pdf_sha256=huella, documento_listo=False)
            guardar_estado(estado)
        almacen_id = estado["vector_store_id"]

        # If the wait was interrupted, recover the file that was already uploaded.
        archivos = list(cliente.vector_stores.files.list(vector_store_id=almacen_id))
        if len(archivos) > 1:
            raise ValueError("The Vector Store contains more than one file; check it before continuing.")
        if archivos:
            archivo = archivos[0]
            estado.update(file_id=archivo.id, documento_listo=False)
            guardar_estado(estado)
            archivo = cliente.vector_stores.files.poll(
                vector_store_id=almacen_id, file_id=archivo.id,
            )
            print("Reusing the existing document.")
        else:
            if estado.get("file_id") or estado.get("documento_listo"):
                print("The document was removed from the Vector Store. It will be uploaded again.")
            estado.update(file_id=None, documento_listo=False)
            estado.pop("agent_version", None)
            guardar_estado(estado)
            print("Uploading and indexing the PDF...")
            with documento.open("rb") as contenido:
                archivo = cliente.vector_stores.files.upload_and_poll(
                    vector_store_id=almacen_id, file=contenido,
                )

        # The helper waits for indexing; we also check whether an error occurred.
        estado.update(file_id=archivo.id, documento_listo=archivo.status == "completed")
        guardar_estado(estado)
        if not estado["documento_listo"]:
            raise ValueError(f"Indexing: {archivo.status}. Details: {archivo.last_error}")
        print(f"Vector Store: {almacen_id}\nFile: {archivo.id}\nIndexing completed.")
        print("IDs saved to estado.json. Next step: 03_agente.py")


if __name__ == "__main__":
    ejecutar(main)