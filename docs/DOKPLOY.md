# Deploy no Dokploy — Vulcano 2.0

## Compose

- **Compose path:** `docker-compose.yml` (na raiz do repo, pasta `code/` após clone)
- **Tipo:** Docker Compose (não Stack)
- Use **Deploy** (não **Rebuild**): Rebuild não clona o Git de novo; sem clone o arquivo some e aparece `Compose file not found`.

## Environment (obrigatório editar no painel)

```env
VITE_API_BASE=https://api.SEU_DOMINIO
DB_PATH_VULCANO=/caminho/no/servidor-firebird/VULCANO.FDB
DB_PATH_QUESTOR=/caminho/no/servidor-firebird/Questor.fdb
FIREBIRD_HOST=IP_DO_LINUX_FIREBIRD
FIREBIRD_PORT=3050
FIREBIRD_USER=SYSDBA
FIREBIRD_PASSWORD=
GOOGLE_APPLICATION_CREDENTIALS=chave_fernando.json
```

## Chave Vertex (GCP)

**Advanced → Mounts → File Mount**

- Caminho no host Dokploy: `../files/chave_fernando.json`
- Conteúdo: JSON da service account

Sem este arquivo o deploy do backend falha no bind mount.

## Domínios

| Serviço    | Porta container |
|-----------|-----------------|
| frontend  | 80              |
| backend   | 8000            |

Após criar domínios, ajuste `VITE_API_BASE` e faça redeploy com rebuild do frontend.

## Firebird

Liberar TCP **3050** no servidor Firebird para o IP do host Dokploy.
