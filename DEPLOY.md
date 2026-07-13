# Deploy no Render — web-scraper-tool

## O que foi alterado

O projeto original é uma ferramenta de linha de comando interativa.  
Para o deploy no Render (que exige um servidor HTTP), foi adicionado um ficheiro `api.py` que expõe as funcionalidades como uma **API REST com FastAPI**.

Ficheiros adicionados:
- `Dockerfile` — build da imagem com Python 3.11 + ffmpeg + yt-dlp
- `api.py` — servidor FastAPI que envolve a lógica do `web_scraper.py`
- `render.yaml` — configuração de deploy automático no Render
- `requirements.txt` — atualizado com `fastapi` e `uvicorn`

---

## Deploy no Render (passo a passo)

### 1. Fazer fork / push do repositório

Certifica-te de que os ficheiros acima estão no teu repositório GitHub/GitLab.

### 2. Criar serviço no Render

1. Acede a [render.com](https://render.com) e faz login
2. Clica em **New → Web Service**
3. Liga o teu repositório GitHub
4. Render vai detetar automaticamente o `Dockerfile`
5. Configura:
   - **Name:** `web-scraper-tool` (ou o que quiseres)
   - **Region:** Frankfurt (mais próximo de Barcelona)
   - **Branch:** `master`
   - **Runtime:** Docker *(detetado automaticamente)*
   - **Plan:** Free
6. Em **Environment Variables**, adiciona se necessário:
   - `PORT` = `8000`
   - `DOWNLOAD_DIR` = `/app/downloads`
7. Clica em **Create Web Service**

---

## Endpoints disponíveis

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Health check + lista de endpoints |
| `GET` | `/search?q=termo` | Pesquisa DuckDuckGo |
| `POST` | `/scrape/text` | Extrai texto por CSS selector |
| `POST` | `/scrape/links` | Extrai links por CSS selector |
| `POST` | `/scrape/images` | Extrai imagens por CSS selector |
| `POST` | `/video` | Extrai URL de download de vídeo |
| `GET` | `/downloads` | Lista ficheiros no diretório de downloads |

Documentação interativa (Swagger): `https://SEU-SERVICO.onrender.com/docs`

---

## Exemplos de uso

```bash
# Pesquisa
curl "https://SEU-SERVICO.onrender.com/search?q=python+tutorial"

# Scrape de texto
curl -X POST "https://SEU-SERVICO.onrender.com/scrape/text" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "selector": "p"}'

# Download de vídeo TikTok (retorna a URL, não descarrega)
curl -X POST "https://SEU-SERVICO.onrender.com/video" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.tiktok.com/@user/video/123", "quality": "best"}'
```

---

## Nota importante

No plano **Free** do Render, o serviço entra em modo sleep após 15 minutos de inatividade.  
O primeiro request após o sleep pode demorar 30-60 segundos a responder.  
Para evitar isso, considera o plano **Starter** ($7/mês).
