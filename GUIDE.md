# Demo script: a document agent with Microsoft Foundry

**English** | [Español](GUIA.md) · Setup and details: [README.md](README.md)

## Before the presentation

Fill in the endpoint and the deployment name in `.env` (copy it from
`.env.example`). Sign in with your Microsoft Entra ID account, with permissions
on the project. Do not show tokens, passwords or credentials during the
presentation.

Open the demo folder in VS Code and activate the virtual environment:

```powershell
. .\.venv\Scripts\Activate.ps1
```

File names, variables and `estado.json` keys are in Spanish; messages, errors
and agent instructions are in English. The agent answers in the language of the
question, so the audience can ask in English or Spanish.

## 1. The model

Open `01_modelo.py` and run:

```powershell
python 01_modelo.py
```

Explain: "An LLM is a model that generates language. The deployment is the
instance of the model we use; the endpoint is the address of the project. The
code authenticates with Microsoft Entra ID and sends a question through the
Responses API."

Show the question in the code and the answer in the terminal. At this stage the
model does not have access to the company handbook yet.

## 2. The document

Open `documentos/manual_empresa.pdf` and show the concrete policy values.
Then run:

```powershell
python 02_documento.py
```

Explain: "RAG means retrieving information before generating the answer. File
Search splits the document into chunks and indexes the content. Embeddings
represent similarity of meaning. The Vector Store lets us find the relevant
passages without setting up a database or a search engine."

Show the Vector Store ID and the file ID. Run it again to show reuse. To repeat
the upload, delete the document or the Vector Store in Foundry and run phase 2
again. Do not delete `estado.json`.

## 3. The agent

Open `03_agente.py` and run:

```powershell
python 03_agente.py
```

Explain: "On its own, the model generates answers. The agent combines that model
with instructions and tools. We create everything in Python; Foundry runs the
Prompt Agent logic and the File Search calls."

Read the instructions: answer only with information grounded in the document,
admit when the information is not available, answer in the language of the
question and include references when they exist. Show the agent name and version.

## 4. The conversation

Open `04_chat.py` and run:

```powershell
python 04_chat.py
```

Enter one question at a time:

| Question | Expected information |
| --- | --- |
| How many vacation days does an employee get? | 24 working days per year. |
| How far in advance must they be requested? | 15 calendar days; uses the context of the previous question. |
| What is the remote work policy? | Two days per week with approval; Wednesdays on site. |
| How do I claim reimbursement for travel expenses? | Form GV-17, invoices and receipts, within 10 calendar days of returning. |
| What training does the company offer? | AI, cybersecurity and communication; 600 euros and 20 hours per year. |
| What is the CEO's salary? | The information is not available in the document. |

You can also use: "I'm going on a business trip. What are the expense policies?"

Show the `Source:` lines when available. Explain: "The conversation keeps the
context. References help verify where the answer comes from. When the document
does not contain the information, the agent should admit it instead of making
up an answer." The instructions do not guarantee the absence of errors.

Type `exit` to finish (`salir` and `sair` also work). After deleting and
recovering resources, run phase 3 again and open a new chat to use the updated
link.

## Checks and wrap-up

- Confirm the answers and at least one reference to the PDF.
- Confirm context between questions and that missing information is admitted.
- Repeat phases 2 and 3 without creating unnecessary resources.
- Do not use real data: the handbook only contains fictitious information.
- Remember that tokens, File Search calls and storage can have costs.
- Closing the program does not delete resources or conversations in Foundry.
- Manually delete only the demo resources when they are no longer needed.

Local tests, without calls to Azure:

```powershell
python -m unittest -v test_demo
```
