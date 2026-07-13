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
from ddgs import DDGS
from apify_client import ApifyClient

app = FastAPI(
    title="Web Scraper + Video Download API",
    description="API para scraping web e download de vídeos (Instagram, TikTok, YouTube, Twitter, etc.)",
    version="2.1.0",
)

# Definir o caminho base absoluto (onde o api.py está localizado)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "/app/downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Configuração do Apify (Pega o token das variáveis de ambiente do Render)
APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
apify_client = ApifyClient(APIFY_TOKEN) if APIFY_TOKEN else None

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ─── Configurar arquivos estáticos ─────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=PUBLIC_DIR), name="static")

# ─── Models ────────────────────────────────────────────────────────────────────
class ScrapeRequest(BaseModel):
    url: str
    selector: str = "p"

class VideoRequest(BaseModel):
    url: str
    quality: str = "best"  # best | 720 | 480 | 360

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
        "apify_status": "Conectado" if apify_client else "Desconectado (Token do Apify não encontrado)",
        "endpoints": [
            "GET  /api/search?q=python+tutorial&platform=all&sort_by=relevance",
            "POST /api/scrape/text   - extrai texto por CSS selector",
            "POST /api/scrape/links  - extrai links por CSS selector",
            "POST /api/scrape/images - extrai imagens por CSS selector",
            "POST /api/video         - extrai URL de download de vídeo",
            "GET  /api/downloads     - lista ficheiros descarregados",
        ],
    }

@app.get("/api/search")
def web_search(
    q: str = Query(..., description="Termo de pesquisa"), 
    num: int = 10, 
    platform: str = Query("all", description="Filtrar por rede social"),
    sort_by: str = Query("relevance", description="Ordenar por: relevance, views, likes")
):
    """Pesquisa na web. Usa Apify para TikTok, DDGS/Bing para o resto."""
    results = []
    
    # Se for TikTok e tiver Apify configurado, usa o Apify!
    if platform == "tiktok" and apify_client:
        try:
            print(f"Usando Apify para buscar no TikTok: {q}")
            search_term = q.lstrip('#')
            
            # Pedimos um pouco mais de resultados ao Apify para poder ordenar e cortar depois
            fetch_num = num if sort_by == "relevance" else num * 3
            
            run_input = {
                "hashtags": [search_term],
                "resultsPerPage": fetch_num,
                "shouldDownloadCovers": False,
                "shouldDownloadSlideshowImages": False,
                "shouldDownloadSubtitles": False,
                "shouldDownloadVideos": False
            }
            
            run = apify_client.actor("clockworks/tiktok-scraper").call(run_input=run_input)
            
            temp_results = []
            for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                temp_results.append({
                    "title": item.get("text", "")[:80] + "..." if len(item.get("text", "")) > 80 else item.get("text", ""),
                    "url": item.get("webVideoUrl", ""),
                    "description": item.get("text", ""),
                    "author": item.get("authorMeta", {}).get("name", ""),
                    "video_url": item.get("videoUrl"),
                    "views": item.get("playCount", 0),
                    "likes": item.get("diggCount", 0)
                })
            
            # Lógica de Ordenação
            if sort_by == "views":
                temp_results.sort(key=lambda x: x.get("views", 0), reverse=True)
            elif sort_by == "likes":
                temp_results.sort(key=lambda x: x.get("likes", 0), reverse=True)
                
            # Corta para o número exato que o usuário pediu
            results = temp_results[:num]
            
            return {"query": q, "platform": "tiktok", "count": len(results), "results": results, "engine": "Apify (TikTok Scraper)"}
            
        except Exception as apify_error:
            print(f"Erro no Apify: {apify_error}. Tentando busca normal...")

    # Busca normal (DuckDuckGo e Bing) para outras plataformas
    search_query = q
    if platform != "all":
        search_query += f" site:{platform}.com"
    
    try:
        with DDGS() as ddgs:
            ddgs_results = list(ddgs.text(search_query, max_results=num))
            for r in ddgs_results:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href") or r.get("link") or r.get("url", ""),
                    "description": r.get("body") or r.get("snippet", "")
                })
    except Exception as ddg_error:
        print(f"ddgs falhou: {ddg_error}. Tentando Bing...")

    if not results:
        try:
            url = f"https://www.bing.com/search?q={requests.utils.quote(search_query)}&count={num}"
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for item in soup.select("li.b_algo"):
                title_el = item.select_one("h2 a")
                desc_el = item.select_one(".b_caption p")
                if title_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": title_el.get("href", ""),
                        "description": desc_el.get_text(strip=True) if desc_el else "",
                    })
        except Exception as bing_error:
            print(f"Erro no Bing: {bing_error}")

    if not results:
        raise HTTPException(status_code=404, detail="Nenhum resultado encontrado. Verifique se o Token do Apify está configurado para TikTok.")

    return {"query": q, "platform": platform, "count": len(results), "results": results, "engine": "DuckDuckGo/Bing"}

@app.post("/api/scrape/text")
def scrape_text(req: ScrapeRequest):
    try:
        html = fetch_html(clean_url(req.url))
        soup = BeautifulSoup(html, "html.parser")
        elements = [el.get_text(strip=True) for el in soup.select(req.selector)]
        return {"url": req.url, "selector": req.selector, "count": len(elements), "data": elements}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape/links")
def scrape_links(req: ScrapeRequest):
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
    Extrai a URL de download do vídeo.
    Usa Apify para TikTok (se token configurado), yt-dlp para o resto.
    """
    url = clean_url(req.url)
    
    # Se for TikTok e tiver Apify, usa o Apify para não tomar bloqueio
    if "tiktok.com" in url and apify_client:
        try:
            print("Usando Apify para extrair vídeo do TikTok...")
            run_input = {
                "postURLs": [url],
                "shouldDownloadVideos": False
            }
            run = apify_client.actor("clockworks/tiktok-scraper").call(run_input=run_input)
            
            for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                return {
                    "status": "success",
                    "source_url": url,
                    "title": item.get("text", ""),
                    "author": item.get("authorMeta", {}).get("name", ""),
                    "download_urls": [item.get("videoUrl")]
                }
            raise HTTPException(status_code=400, detail="Apify não retornou dados para este link.")
        except Exception as apify_error:
            raise HTTPException(status_code=500, detail=f"Erro no Apify: {str(apify_error)}")

    # Para outras plataformas (YouTube, Twitter, etc), usa yt-dlp
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
            cmd_json = ["yt-dlp", "--dump-json", "--no-playlist", "--no-warnings", url]
            result_json = subprocess.run(cmd_json, capture_output=True, text=True, timeout=60)
            
            if result_json.returncode == 0 and result_json.stdout.strip():
                try:
                    info = json.loads(result_json.stdout)
                    return {
                        "status": "success",
                        "title": info.get("title"),
                        "download_url": info.get("url"),
                    }
                except json.JSONDecodeError:
                    pass
            
            error_msg = result.stderr.strip().split('\n')[-1] or "yt-dlp falhou. A plataforma pode estar bloqueando o servidor."
            raise HTTPException(status_code=400, detail=error_msg)
            
        download_urls = [u for u in result.stdout.strip().split("\n") if u.startswith("http")]
        if not download_urls:
            raise HTTPException(status_code=400, detail="Nenhuma URL de download direto encontrada.")
            
        return {
            "status": "success",
            "source_url": url,
            "quality": req.quality,
            "download_urls": download_urls,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Timeout ao extrair vídeo (60s).")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

@app.get("/api/downloads")
def list_downloads():
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
    index_path = os.path.join(PUBLIC_DIR, "index.html")
    if not os.path.exists(index_path):
        return HTMLResponse(content="<h1>Erro: index.html não encontrado em public/</h1>", status_code=404)
    return FileResponse(index_path)

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": time.time()}
