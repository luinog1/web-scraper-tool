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
@app.get("/api")
def api_root():
    return {
        "message": "Web Scraper API is running.",
        "endpoints": [
            "GET  /api/search?q=python+tutorial",
            "POST /api/scrape/text   - extrai texto por CSS selector",
            "POST /api/scrape/links  - extrai links por CSS selector",
            "POST /api/scrape/images - extrai imagens por CSS selector",
            "POST /api/video         - extrai URL de download de vídeo",
            "GET  /api/downloads     - lista ficheiros descarregados",
        ],
    }

@app.get("/api/search")
def web_search(q: str = Query(..., description="Termo de pesquisa"), num: int = 10):
    """Pesquisa no DuckDuckGo e devolve os resultados."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(q)}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for item in soup.select("div.result")[:num]:
            title_el = item.select_one("a.result__a")
            desc_el = item.select_one("a.result__snippet")
            if title_el:
                results.append({
                    "title": title_el.get_text(strip=True),
                    "url": title_el.get("href", ""),
                    "description": desc_el.get_text(strip=True) if desc_el else "",
                })
        return {"query": q, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape/text")
def scrape_text(req: ScrapeRequest):
    """Extrai texto de uma página usando um CSS selector."""
    try:
        html = fetch_html(clean_url(req.url))
        soup = BeautifulSoup(html, "html.parser")
        elements = [el.get_text(strip=True) for el in soup.select(req.selector)]
        return {"url": req.url, "selector": req.selector, "count": len(elements), "data": elements}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape/links")
def scrape_links(req: ScrapeRequest):
    """Extrai links de uma página usando um CSS selector."""
    try:
        html = fetch_html(clean_url(req.url))
        soup = BeautifulSoup(html, "html.parser")
        selector = req.selector if req.selector != "p" else "a"
        links = [
            {"text": a.get_text(strip=True), "href": a.get("href", "")}
            for a in soup.select(selector)
        ]
        return {"url": req.url, "selector": selector, "count": len(links), "data": links}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape/images")
def scrape_images(req: ScrapeRequest):
    """Extrai imagens de uma página usando um CSS selector."""
    try:
        html = fetch_html(clean_url(req.url))
        soup = BeautifulSoup(html, "html.parser")
        selector = req.selector if req.selector != "p" else "img"
        images = [
            {"src": img.get("src", ""), "alt": img.get("alt", "")}
            for img in soup.select(selector)
        ]
        return {"url": req.url, "selector": selector, "count": len(images), "data": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/video")
def get_video_info(req: VideoRequest):
    """
    Extrai a URL de download do vídeo usando yt-dlp (sem descarregar o ficheiro).
    Suporta: YouTube, TikTok, Instagram, Twitter/X, Facebook, e muito mais.
    """
    url = clean_url(req.url)
    quality_map = {
        "best": "bestvideo+bestaudio/best",
        "720": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "480": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "360": "bestvideo[height<=360]+bestaudio/best[height<=360]",
    }
    fmt = quality_map.get(req.quality, "bestvideo+bestaudio/best")
    try:
        cmd = [
            "yt-dlp",
            "--get-url",
            "--no-playlist",
            "--no-warnings",
            "-f", fmt,
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            # Fallback: tentar obter metadados em JSON
            cmd_json = ["yt-dlp", "--dump-json", "--no-playlist", "--no-warnings", url]
            result_json = subprocess.run(cmd_json, capture_output=True, text=True, timeout=60)
            if result_json.returncode == 0:
                info = json.loads(result_json.stdout)
                return {
                    "status": "success",
                    "title": info.get("title"),
                    "uploader": info.get("uploader"),
                    "duration": info.get("duration"),
                    "thumbnail": info.get("thumbnail"),
                    "download_url": info.get("url"),
                    "formats_available": len(info.get("formats", [])),
                }
            raise HTTPException(status_code=400, detail=result.stderr.strip() or "yt-dlp falhou")
        download_urls = [u for u in result.stdout.strip().split("\n") if u.startswith("http")]
        return {
            "status": "success",
            "source_url": url,
            "quality": req.quality,
            "download_urls": download_urls,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Timeout ao extrair vídeo (60s)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/downloads")
def list_downloads():
    """Lista os ficheiros presentes no diretório de downloads do container."""
    try:
        files = []
        for f in os.listdir(DOWNLOAD_DIR):
            path = os.path.join(DOWNLOAD_DIR, f)
            size = os.path.getsize(path)
            files.append({"name": f, "size_bytes": size, "size_mb": round(size / 1024 / 1024, 2)})
        return {"download_dir": DOWNLOAD_DIR, "count": len(files), "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
