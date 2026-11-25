# Security policy / Política de seguridad

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Use
[GitHub private vulnerability reporting](../../security/advisories/new) instead.

## Using this demo safely

- Never commit `.env`, `estado.json`, keys, tokens or connection strings. They
  are already listed in `.gitignore`; check `git status` before every commit.
- The code authenticates with Microsoft Entra ID (`DefaultAzureCredential`) and
  needs no API keys. Grant only the **Foundry User** role on the project.
- Use fictitious documents only. File Search does not provide per-user or
  per-document access control.
- Delete the demo resources in Foundry when you finish; see the README.

---

## Notificar una vulnerabilidad

Por favor, **no abras un issue público** para problemas de seguridad. Usa el
[reporte privado de vulnerabilidades de GitHub](../../security/advisories/new).

## Uso seguro de la demo

- No subas nunca `.env`, `estado.json`, claves, tokens ni cadenas de conexión.
  Ya están en `.gitignore`; revisa `git status` antes de cada commit.
- El código se autentica con Microsoft Entra ID (`DefaultAzureCredential`) y no
  necesita API keys. Asigna solo el rol **Foundry User** en el proyecto.
- Usa solo documentos ficticios. File Search no ofrece control de acceso por
  usuario ni por documento.
- Elimina los recursos de la demo en Foundry al terminar; consulta el README.
