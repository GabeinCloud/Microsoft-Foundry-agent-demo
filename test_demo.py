"""Tests without network or credentials: python -m unittest -v test_demo."""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
from azure.ai.projects import AIProjectClient
from azure.core.credentials import AccessToken
from openai import NotFoundError, PermissionDeniedError

import comun
import crear_pdf


def cargar(nombre):
    especificacion = importlib.util.spec_from_file_location(nombre, comun.RAIZ / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


MODELO = cargar("01_modelo")
DOCUMENTO = cargar("02_documento")
AGENTE = cargar("03_agente")
CHAT = cargar("04_chat")
ENDPOINT = "https://demo.services.ai.azure.com/api/projects/demo"


@contextmanager
def clientes_simulados(modulo):
    proyecto, cliente = MagicMock(), MagicMock()
    proyecto.get_openai_client.return_value.__enter__.return_value = cliente
    with (
        patch.object(modulo, "DefaultAzureCredential"),
        patch.object(modulo, "AIProjectClient") as constructor,
    ):
        constructor.return_value.__enter__.return_value = proyecto
        yield proyecto, cliente


def respuesta(texto="24 working days."):
    cita = SimpleNamespace(type="file_citation", filename="manual_empresa.pdf", file_id="file_demo")
    contenido = SimpleNamespace(type="output_text", text=texto, annotations=[cita])
    mensaje = SimpleNamespace(type="message", content=[contenido])
    return SimpleNamespace(status="completed", output_text=texto, output=[mensaje])


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory(dir=comun.RAIZ / ".venv")
        self.addCleanup(self.temporal.cleanup)
        self.raiz = Path(self.temporal.name)
        self.addCleanup(patch.stopall)
        patch.object(comun, "ESTADO", self.raiz / "estado.json").start()
        patch.dict("os.environ", {
            "FOUNDRY_PROJECT_ENDPOINT": ENDPOINT,
            "FOUNDRY_MODEL_DEPLOYMENT_NAME": "deployment_demo",
            "AGENT_NAME": "DocumentAssistant",
        }).start()
        self.salida = io.StringIO()
        self.captura = redirect_stdout(self.salida)
        self.captura.__enter__()
        self.addCleanup(self.captura.__exit__, None, None, None)

    def estado_listo(self):
        estado = {
            "project_endpoint": ENDPOINT, "vector_store_id": "vs_demo",
            "file_id": "file_demo", "documento_listo": True,
            "agent_name": "DocumentAssistant", "agent_version": "1", "model": "deployment_demo",
        }
        comun.guardar_estado(estado)
        return estado

    def test_configuracion_incompleta_no_contacta_azure(self):
        with patch.dict("os.environ", {"FOUNDRY_PROJECT_ENDPOINT": ""}):
            with self.assertRaisesRegex(ValueError, "Fill in"):
                MODELO.main()

    def test_placeholders_de_env_example_no_contactan_azure(self):
        with patch.dict("os.environ", {
            "FOUNDRY_PROJECT_ENDPOINT": "https://YOUR_RESOURCE.services.ai.azure.com/api/projects/YOUR_PROJECT",
            "FOUNDRY_MODEL_DEPLOYMENT_NAME": "YOUR_DEPLOYMENT_NAME",
        }), clientes_simulados(MODELO) as (proyecto, _):
            with self.assertRaisesRegex(ValueError, "placeholders"):
                MODELO.main()
            proyecto.get_openai_client.assert_not_called()

    def test_estado_atomico_y_proyecto_distinto(self):
        estado = self.estado_listo()
        self.assertEqual(comun.cargar_estado(ENDPOINT), estado)
        self.assertFalse(comun.ESTADO.with_suffix(".tmp").exists())
        with self.assertRaisesRegex(ValueError, "another project"):
            comun.cargar_estado("https://otro.services.ai.azure.com/api/projects/otro")

    def test_modelo_usa_deployment_y_responses(self):
        with clientes_simulados(MODELO) as (_, cliente):
            cliente.responses.create.return_value = respuesta()
            MODELO.main()
            self.assertEqual(cliente.responses.create.call_args.kwargs["model"], "deployment_demo")
            self.assertIn("English", cliente.responses.create.call_args.kwargs["input"])

    def test_documento_se_sube_solo_una_vez(self):
        archivo = SimpleNamespace(id="file_demo", status="completed", last_error=None)
        with clientes_simulados(DOCUMENTO) as (_, cliente):
            cliente.vector_stores.create.return_value.id = "vs_demo"
            cliente.vector_stores.files.list.side_effect = [[], [archivo]]
            cliente.vector_stores.files.upload_and_poll.return_value = archivo
            cliente.vector_stores.files.poll.return_value = archivo
            DOCUMENTO.main()
            DOCUMENTO.main()
            cliente.vector_stores.create.assert_called_once()
            cliente.vector_stores.files.upload_and_poll.assert_called_once()
            self.assertTrue(comun.cargar_estado(ENDPOINT)["documento_listo"])

    def test_almacen_borrado_se_recrea_e_invalida_agente(self):
        self.estado_listo()
        error = NotFoundError("No vector store found", response=httpx.Response(
            404, request=httpx.Request("GET", "https://demo.example/vector_stores/vs_demo"),
        ), body=None)
        archivo = SimpleNamespace(id="file_nuevo", status="completed", last_error=None)
        with clientes_simulados(DOCUMENTO) as (_, cliente):
            cliente.vector_stores.retrieve.side_effect = error
            cliente.vector_stores.create.return_value.id = "vs_nuevo"
            cliente.vector_stores.files.list.return_value = []
            cliente.vector_stores.files.upload_and_poll.return_value = archivo
            DOCUMENTO.main()
            cliente.vector_stores.create.assert_called_once()
            cliente.vector_stores.files.upload_and_poll.assert_called_once()
            estado = comun.cargar_estado(ENDPOINT)
            self.assertEqual(estado["vector_store_id"], "vs_nuevo")
            self.assertEqual(estado["file_id"], "file_nuevo")
            self.assertTrue(estado["documento_listo"])
            self.assertNotIn("agent_version", estado)

    def test_archivo_borrado_se_sube_al_mismo_almacen(self):
        self.estado_listo()
        archivo = SimpleNamespace(id="file_nuevo", status="completed", last_error=None)
        with clientes_simulados(DOCUMENTO) as (_, cliente):
            cliente.vector_stores.files.list.return_value = []
            cliente.vector_stores.files.upload_and_poll.return_value = archivo
            DOCUMENTO.main()
            cliente.vector_stores.create.assert_not_called()
            cliente.vector_stores.files.upload_and_poll.assert_called_once()
            estado = comun.cargar_estado(ENDPOINT)
            self.assertEqual(estado["vector_store_id"], "vs_demo")
            self.assertEqual(estado["file_id"], "file_nuevo")
            self.assertNotIn("agent_version", estado)

    def test_error_de_permisos_no_recrea_almacen(self):
        anterior = self.estado_listo()
        error = PermissionDeniedError("Forbidden", response=httpx.Response(
            403, request=httpx.Request("GET", "https://demo.example/vector_stores/vs_demo"),
        ), body=None)
        with clientes_simulados(DOCUMENTO) as (_, cliente):
            cliente.vector_stores.retrieve.side_effect = error
            with self.assertRaises(PermissionDeniedError):
                DOCUMENTO.main()
            cliente.vector_stores.create.assert_not_called()
            cliente.vector_stores.files.upload_and_poll.assert_not_called()
            self.assertEqual(comun.cargar_estado(ENDPOINT), anterior)

    def test_indexacion_fallida_no_habilita_agente(self):
        archivo = SimpleNamespace(id="file_demo", status="failed", last_error="Invalid PDF")
        with clientes_simulados(DOCUMENTO) as (_, cliente):
            cliente.vector_stores.create.return_value.id = "vs_demo"
            cliente.vector_stores.files.list.return_value = []
            cliente.vector_stores.files.upload_and_poll.return_value = archivo
            with self.assertRaisesRegex(ValueError, "Indexing: failed"):
                DOCUMENTO.main()
            estado = comun.cargar_estado(ENDPOINT)
            self.assertEqual(estado["file_id"], "file_demo")
            with self.assertRaises(ValueError):
                comun.exigir_documento(estado)

    def test_pdf_modificado_no_se_vuelve_a_subir(self):
        estado = self.estado_listo()
        estado["pdf_sha256"] = "huella_distinta"
        comun.guardar_estado(estado)
        with clientes_simulados(DOCUMENTO) as (proyecto, _):
            with self.assertRaisesRegex(ValueError, "PDF has changed"):
                DOCUMENTO.main()
            proyecto.get_openai_client.assert_not_called()

    def test_agente_reutiliza_version_y_obliga_file_search(self):
        self.estado_listo()
        with clientes_simulados(AGENTE) as (proyecto, cliente):
            cliente.vector_stores.retrieve.return_value.status = "completed"
            creado = SimpleNamespace(name="DocumentAssistant", version="1", metadata={})
            proyecto.agents.list_versions.side_effect = [[], [creado]]

            def crear(**argumentos):
                creado.metadata = argumentos["metadata"]
                return creado

            proyecto.agents.create_version.side_effect = crear
            AGENTE.main()
            AGENTE.main()
            proyecto.agents.create_version.assert_called_once()
            definicion = proyecto.agents.create_version.call_args.kwargs["definition"].as_dict()
            self.assertEqual(definicion["tool_choice"], "required")
            self.assertEqual(definicion["tools"][0]["vector_store_ids"], ["vs_demo"])
            self.assertIn("same language as the user's question", definicion["instructions"])

    def test_chat_mantiene_conversacion_version_y_citas(self):
        self.estado_listo()
        with clientes_simulados(CHAT) as (proyecto, cliente):
            proyecto.agents.get_version.return_value = SimpleNamespace(name="DocumentAssistant", version="1")
            cliente.conversations.create.return_value.id = "conv_demo"
            cliente.responses.create.return_value = respuesta()
            with patch("builtins.input", side_effect=["Vacation?", "And how far in advance?", "", "EXIT"]):
                CHAT.main()
            cliente.conversations.create.assert_called_once()
            self.assertEqual(cliente.responses.create.call_count, 2)
            for llamada in cliente.responses.create.call_args_list:
                self.assertEqual(llamada.kwargs["conversation"], "conv_demo")
                self.assertEqual(llamada.kwargs["extra_body"]["agent_reference"]["version"], "1")
            self.assertIn("Source: manual_empresa.pdf (file_demo)", self.salida.getvalue())

    def test_chat_exit_salir_y_sair_terminan_sin_consultar_modelo(self):
        self.estado_listo()
        for comando in ("EXIT", "salir", "Sair"):
            with self.subTest(comando=comando), clientes_simulados(CHAT) as (proyecto, cliente):
                proyecto.agents.get_version.return_value = SimpleNamespace(name="DocumentAssistant", version="1")
                with patch("builtins.input", return_value=comando):
                    CHAT.main()
                cliente.responses.create.assert_not_called()
        self.assertIn("Type a question or 'exit'.", self.salida.getvalue())

    def test_chat_sin_agente_no_crea_recursos(self):
        estado = self.estado_listo()
        estado.pop("agent_version")
        comun.guardar_estado(estado)
        with clientes_simulados(CHAT) as (proyecto, _):
            with self.assertRaisesRegex(ValueError, "03_agente"):
                CHAT.main()
            proyecto.get_openai_client.assert_not_called()

    def test_pdf_determinista_y_dos_paginas(self):
        with patch.object(crear_pdf, "DESTINO", self.raiz / "documentos" / "manual.pdf"):
            crear_pdf.main()
            primera_huella = sha256(crear_pdf.DESTINO.read_bytes()).hexdigest()
            crear_pdf.main()
            self.assertEqual(primera_huella, sha256(crear_pdf.DESTINO.read_bytes()).hexdigest())
            self.assertEqual(self.salida.getvalue().count("Pages: 2"), 2)

    def test_sdk_serializa_referencia_y_citas_sin_red(self):
        peticiones = []

        class CredencialLocal:
            def get_token(self, *scopes, **kwargs):
                return AccessToken("solo-test", 9999999999)

        def servidor_local(peticion):
            peticiones.append(peticion)
            return httpx.Response(200, json={
                "id": "resp_demo", "object": "response", "created_at": 0,
                "status": "completed", "model": "deployment_demo",
                "output": [{"id": "msg_demo", "type": "message", "role": "assistant",
                            "status": "completed", "content": [{"type": "output_text",
                            "text": "24 days", "annotations": [{"type": "file_citation",
                            "file_id": "file_demo", "filename": "manual_empresa.pdf", "index": 0}]}]}],
            })

        with (
            httpx.Client(transport=httpx.MockTransport(servidor_local)) as http,
            AIProjectClient(endpoint=ENDPOINT, credential=CredencialLocal()) as proyecto,
            proyecto.get_openai_client(http_client=http) as cliente,
        ):
            resultado = cliente.responses.create(
                conversation="conv_demo", input="Vacation?",
                extra_body={"agent_reference": {"name": "DocumentAssistant", "version": "1",
                                                "type": "agent_reference"}},
            )
            CHAT.mostrar_respuesta(resultado)
        self.assertEqual(len(peticiones), 1)
        self.assertIn("/api/projects/demo/openai/v1/responses", str(peticiones[0].url))
        cuerpo = json.loads(peticiones[0].content)
        self.assertEqual(cuerpo["agent_reference"]["version"], "1")
        self.assertIn("Source: manual_empresa.pdf (file_demo)", self.salida.getvalue())


if __name__ == "__main__":
    unittest.main()