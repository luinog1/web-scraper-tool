"""
API wrapper para o web-scraper-tool.
Expõe as funcionalidades da CLI original como endpoints HTTP.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os, re, time, requests, subprocess, json
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup

app = FastAPI(
    title="Web Scraper + Video Download API",
    description="API para scraping web e download de vídeos (Instagram, TikTok, YouTube, Twitter, etc.)",
    version="1.0.0",
)

DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "/app/downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ─── Configurar arquivos estáticos ─────────────────────────────────────────────
# Montar diretório público para servir arquivos estáticos (CSS, JS, imagens)
app.mount("/static", StaticFiles(directory="public"), name="static")

# ─── Models ────────────────────────────────────────────────────────────────────
class ScrapeRequest(BaseModel):
    url: str
    selector: str = "p"

class VideoRequest(BaseModel):
    url: str
    quality: str = "best"  # best | 720 | 480 | 360

class SearchRequest(BaseModel):
    query: str
    num: int = 10

# ─── Helpers ───────────────────────────────────────────────────────────────────
def clean_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url

def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

# ─── Endpoints da API ──────────────────────────────────────────────────────────
@app.get("/api/search")
def web_search(q: str = Query(..., description="Termo de pesquisa"), num: int = 10):
    """Pesquisa no DuckDuckGo (fallback para Bing) e devolve os resultados."""
    results = []
    
    # TENTATIVA 1: DuckDuckGo
    try:
        url = f"https://duckduckgo.com/html/?q={requests.utils.quote(q)}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for item in soup.select("div.result")[:num]:
            title_el = item.select_one("a.result__a")
            desc_el = item.select_one("a.result__snippet")
            if title_el:
                results.append({
                    "title": title_el.get_text(strip=True),
                    "url": title_el.get("href", ""),
                    "description": desc_el.get_text(strip=True) if desc_el else "",
                })
    except Exception as ddg_error:
        print(f"DuckDuckGo falhou: {ddg_error}. Tentando Bing...")
    
    # TENTATIVA 2: Bing (se DuckDuckGo falhar ou não retornar nada)
    if not results:
        try:
            url = f"https://www.bing.com/search?q={requests.utils.quote(q)}"
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for item in soup.select("li.b_algo")[:num]:
                title_el = item.select_one("h2 a")
                desc_el = item.select_one(".b_caption p")
                if title_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": title_el.get("href", ""),
                        "description": desc_el.get_text(strip=True) if desc_el else "",
                    })
        except Exception as bing_error:
            raise HTTPException(status_code=500, detail=f"Erro no DuckDuckGo e no Bing: {str(bing_error)}")

    if not results:
        raise HTTPException(status_code=404, detail="Nenhum resultado encontrado em nenhum motor de busca.")

    return {"query": q, "count": len(results), "results": results, "engine": "Bing (Fallback)" if len(results) > 0 else "DuckDuckGo"}

# ─── Servir interface frontend ─────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve a interface frontend principal."""
    return FileResponse("public/index.html")

# ─── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    """Endpoint para verificação de saúde do serviço."""
    return {"status": "healthy", "timestamp": time.time()}
