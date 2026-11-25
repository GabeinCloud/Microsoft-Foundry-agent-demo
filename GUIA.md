# Guion de la demo: un agente documental con Microsoft Foundry

[English](GUIDE.md) | **Español** · Preparación y detalles: [README.es.md](README.es.md)

## Antes de la presentación

Completa el endpoint y el nombre del deployment en `.env` (cópialo desde
`.env.example`). Inicia sesión con tu cuenta de Microsoft Entra ID, con permisos
en el proyecto. No muestres tokens, contraseñas ni credenciales durante la
presentación.

Abre la carpeta de la demo en VS Code y activa el entorno virtual:

```powershell
. .\.venv\Scripts\Activate.ps1
```

Los nombres de archivos, las variables y las claves de `estado.json` están en
español; los mensajes, los errores y las instrucciones del agente están en
inglés. El agente responde en el idioma de la pregunta, así que el público puede
preguntar en español o en inglés.

## 1. El modelo

Abre `01_modelo.py` y ejecuta:

```powershell
python 01_modelo.py
```

Explica: «Un LLM es un modelo que genera lenguaje. El deployment es la instancia
del modelo que utilizamos; el endpoint es la dirección del proyecto. El código se
autentica con Microsoft Entra ID y envía una pregunta a través de la Responses API.»

Muestra la pregunta en el código y la respuesta en el terminal. En esta fase el
modelo todavía no tiene acceso al manual de la empresa.

## 2. El documento

Abre `documentos/manual_empresa.pdf` y muestra los valores concretos de las
políticas. Después ejecuta:

```powershell
python 02_documento.py
```

Explica: «RAG significa recuperar información antes de generar la respuesta.
File Search divide el documento en fragmentos e indexa el contenido. Los
embeddings representan similitud de significado. El Vector Store permite
encontrar los fragmentos relevantes sin configurar una base de datos ni un motor
de búsqueda.»

Muestra el ID del Vector Store y el ID del archivo. Ejecuta de nuevo para
demostrar la reutilización. Para repetir la carga, puedes eliminar el documento
o el Vector Store en Foundry y volver a ejecutar la fase 2. No elimines
`estado.json`.

## 3. El agente

Abre `03_agente.py` y ejecuta:

```powershell
python 03_agente.py
```

Explica: «El modelo, por sí solo, genera respuestas. El agente combina ese modelo
con instrucciones y herramientas. Creamos todo en Python; Foundry ejecuta la
lógica del Prompt Agent y las llamadas a File Search.»

Lee las instrucciones: responder solo con información fundamentada en el
documento, reconocer cuando la información no está disponible, responder en el
idioma de la pregunta e incluir referencias cuando existan. Muestra el nombre y
la versión del agente.

## 4. La conversación

Abre `04_chat.py` y ejecuta:

```powershell
python 04_chat.py
```

Introduce una pregunta cada vez:

| Pregunta | Información esperada |
| --- | --- |
| ¿Cuántos días de vacaciones tiene un empleado? | 24 días laborables al año. |
| ¿Con cuánta antelación se solicitan? | 15 días naturales; usa el contexto de la pregunta anterior. |
| ¿Cuál es la política de teletrabajo? | Dos días por semana con aprobación; los miércoles, presencial. |
| ¿Cómo se solicita el reembolso de los gastos de viaje? | Formulario GV-17, facturas y justificantes, hasta 10 días naturales después del regreso. |
| ¿Qué formación ofrece la empresa? | IA, ciberseguridad y comunicación; 600 euros y 20 horas al año. |
| ¿Cuál es el salario del director general? | La información no está disponible en el documento. |

También puedes usar: «Voy a viajar. ¿Cuáles son las políticas de gastos?»

Muestra las líneas `Source:` cuando aparezcan. Explica: «La conversación mantiene
el contexto. Las referencias ayudan a verificar el origen de la respuesta.
Cuando el documento no contiene la información, el agente debe reconocerlo en
lugar de inventar una respuesta.» Las instrucciones no garantizan la ausencia
de errores.

Escribe `exit` para terminar (`salir` y `sair` también funcionan). Después de
eliminar y recuperar recursos, ejecuta de nuevo la fase 3 y abre un chat nuevo
para usar el enlace actualizado.

## Comprobaciones y cierre

- Confirmar las respuestas y al menos una referencia al PDF.
- Confirmar el contexto entre preguntas y el reconocimiento de información ausente.
- Repetir las fases 2 y 3 sin crear recursos innecesarios.
- No usar datos reales: el manual solo contiene información ficticia.
- Recordar que los tokens, las llamadas a File Search y el almacenamiento pueden tener costes.
- Cerrar el programa no elimina recursos ni conversaciones en Foundry.
- Eliminar manualmente solo los recursos de la demo cuando ya no sean necesarios.

Pruebas locales, sin llamadas a Azure:

```powershell
python -m unittest -v test_demo
```
