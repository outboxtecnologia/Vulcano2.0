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

## Domínios e acesso na rede (LAN)

**Servidor Dokploy:** `http://192.168.19.70:3000` (painel — não é o app).

**Não use** domínios `sslip.io` com IP público errado (ex.: `187-94-101-190`) — o DNS aponta para outro host (ex.: Zimbra). Use IP **LAN** `192-168-19-70` no hostname ou portas publicadas.

| Acesso | URL |
|--------|-----|
| UI (porta publicada) | `http://192.168.19.70:8080` |
| API (porta publicada) | `http://192.168.19.70:8000` |
| UI via Traefik (Host) | `http://192.168.19.70` ou `http://vulcano-explorer-i2rgly-*-192-168-19-70.sslip.io` |
| API via Traefik | `http://api-vulcano-explorer-i2rgly-*-192-168-19-70.sslip.io` |

Environment obrigatório para build do frontend:

```env
VITE_API_BASE=http://192.168.19.70:8000
```

| Serviço    | Porta container |
|-----------|-----------------|
| frontend  | 80 (host `8080:80`) |
| backend   | 8000            |

Após alterar domínios ou `VITE_API_BASE`, faça **Deploy** (rebuild do frontend).

## Firebird

Liberar TCP **3050** no servidor Firebird para o IP do host Dokploy.

Quando `FIREBIRD_HOST` ainda for placeholder, mantenha no Environment:

```env
BOOTSTRAP_TARGET=sqlite
```

Depois de preencher Firebird de verdade, mude para `BOOTSTRAP_TARGET=all` e redeploy.

## Backend unhealthy

Se o log mostrar `backend-1 is unhealthy`:

1. `BOOTSTRAP_TARGET=sqlite` (evita bootstrap travar no Firebird inválido)
2. **Obrigatório para subir o Uvicorn:** Vertex **ou** API key — sem os dois o import do LangGraph quebrava com `API key required for Gemini Developer API`. Corrigido: o app sobe sem IA; configure um dos itens abaixo para agentes/Gemini.
3. **Vertex:** File Mount `../files/chave_fernando.json` → `/app/chave_fernando.json` e `GOOGLE_APPLICATION_CREDENTIALS=chave_fernando.json`
4. **Ou** `GEMINI_API_KEY=` no Environment (Google AI Studio)
5. Logs do container `backend`: aba Logs no Dokploy — procure `ValidationError` / `ChatGoogleGenerativeAI`
