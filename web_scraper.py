import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import os
import re
import subprocess
import sys
import random
from urllib.parse import urlparse, unquote
from colorama import init, Fore, Back, Style

init(autoreset=True)

class Colors:
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    CYAN = Fore.CYAN
    PURPLE = Fore.MAGENTA
    WHITE = Fore.WHITE
    BOLD = Style.BRIGHT
    RESET = Style.RESET_ALL

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def print_slow(text, color=Colors.WHITE, delay=0.03):
    for char in text:
        sys.stdout.write(f"{color}{char}{Colors.RESET}")
        sys.stdout.flush()
        time.sleep(delay)
    print()

def print_ascii_art():
    clear_screen()
    colors = [Colors.RED, Colors.GREEN, Colors.YELLOW, Colors.BLUE, Colors.PURPLE]

    art = r"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     __        _______ ____  ___    ____ _____ _   _ ______   ║
    ║     \ \      / / ____/ ___||__ \  / ___|_   _| | | |  _ \  ║
    ║      \ \ /\ / /|  _| \___ \ / / | |     | | | | | | | | | ║
    ║       \ V  V / | |___ ___) / /_ | |___  | | | |_| | |_| | ║
    ║        \_/\_/  |_____|____/____| \____| |_|  \___/|____/  ║
    ║                                                              ║
    ║            + VIDEO DOWNLOADER + AUTO DETECT                  ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    for line in art.split('\n'):
        color = random.choice(colors)
        print(f"{color}{Colors.BOLD}{line}{Colors.RESET}")
        time.sleep(0.05)

def loading_animation(text, duration=2):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    colors = [Colors.RED, Colors.GREEN, Colors.YELLOW, Colors.BLUE, Colors.PURPLE]
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        sys.stdout.write(f"\r{random.choice(colors)}{frames[i % len(frames)]} {text}{Colors.RESET}   ")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    print(f"\r{Colors.GREEN}✓ {text} Done!{Colors.RESET}   ")

def progress_bar(current, total, prefix="Progress", suffix="Complete", length=40):
    filled = int(length * current / total)
    bar = "█" * filled + "░" * (length - filled)
    percent = current / total * 100
    color = Colors.GREEN if percent == 100 else Colors.YELLOW
    sys.stdout.write(f"\r{Colors.BLUE}{prefix}: {color}{bar} {percent:.1f}% {suffix}{Colors.RESET}")
    sys.stdout.flush()

def print_banner():
    colors = [Colors.RED, Colors.GREEN, Colors.YELLOW, Colors.BLUE, Colors.PURPLE, Colors.WHITE]
    banner = f"""
{Colors.BOLD}{Colors.BLUE}    ╔══════════════════════════════════════════════════════╗
    ║                                                      ║
    ║     🔍 SEARCH    📥 DOWNLOAD    🎬 VIDEOS            ║
    ║                                                      ║
    ║     Instagram | TikTok | YouTube | Twitter           ║
    ║                                                      ║
    ╚══════════════════════════════════════════════════════╝{Colors.RESET}"""
    print(banner)

def print_menu():
    print(f"""
{Colors.BOLD}{Colors.CYAN}    ┌─────────────────────────────────────────┐
    │           {Colors.YELLOW}📋 MAIN MENU{Colors.CYAN}                      │
    ├─────────────────────────────────────────┤
    │                                         │
    │   {Colors.GREEN}1.{Colors.WHITE}  🔍 Web Search{Colors.CYAN}                   │
    │   {Colors.GREEN}2.{Colors.WHITE}  🔎 Website Keyword Search{Colors.CYAN}       │
    │   {Colors.GREEN}3.{Colors.WHITE}  🔗 Website Link Search{Colors.CYAN}          │
    │                                         │
    │   {Colors.GREEN}4.{Colors.WHITE}  📝 Text Scrape{Colors.CYAN}                  │
    │   {Colors.GREEN}5.{Colors.WHITE}  🔗 Links Scrape{Colors.CYAN}                 │
    │   {Colors.GREEN}6.{Colors.WHITE}  🖼️  Images Scrape{Colors.CYAN}                │
    │                                         │
    │   {Colors.GREEN}7.{Colors.WHITE}  🎬 Video Download{Colors.CYAN}               │
    │   {Colors.GREEN}8.{Colors.WHITE}  📥 File Download{Colors.CYAN}                │
    │   {Colors.GREEN}9.{Colors.WHITE}  🖼️  Download All Images{Colors.CYAN}            │
    │                                         │
    │   {Colors.RED}10.{Colors.WHITE} 🚪 Exit{Colors.CYAN}                          │
    │                                         │
    └─────────────────────────────────────────┘{Colors.RESET}""")

def print_success(text):
    print(f"\n{Colors.GREEN}{Colors.BOLD}  ✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"\n{Colors.RED}{Colors.BOLD}  ❌ {text}{Colors.RESET}")

def print_info(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}  ℹ️  {text}{Colors.RESET}")

def print_warning(text):
    print(f"\n{Colors.YELLOW}{Colors.BOLD}  ⚠️  {text}{Colors.RESET}")

class WebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.download_dir = "/storage/emulated/0/only for work/downloads"
        os.makedirs(self.download_dir, exist_ok=True)

    def auto_detect(self, url, data, headers):
        ext = self._detect_from_content_type(headers)
        if ext: return ext
        ext = self._detect_from_url(url)
        if ext: return ext
        ext = self._detect_from_magic(data)
        if ext: return ext
        return 'bin'

    def _detect_from_content_type(self, headers):
        ct = headers.get('Content-Type', '').lower().split(';')[0].strip()
        mime_map = {
            'image/jpeg': 'jpg', 'image/png': 'png', 'image/gif': 'gif',
            'image/webp': 'webp', 'video/mp4': 'mp4', 'video/webm': 'webm',
            'audio/mpeg': 'mp3', 'application/pdf': 'pdf', 'application/zip': 'zip',
            'text/html': 'html', 'text/plain': 'txt',
        }
        return mime_map.get(ct)

    def _detect_from_url(self, url):
        try:
            ext = unquote(urlparse(url).path).split('.')[-1].split('?')[0].lower()
            if ext in ['jpg','png','gif','webp','mp4','webm','mkv','avi','mov','mp3','wav','pdf','zip','txt']:
                return ext
        except: pass
        return None

    def _detect_from_magic(self, data):
        if not data or len(data) < 4: return None
        h = data[:16]
        if h[:8] == b'\x89PNG\r\n\x1a\n': return 'png'
        if h[:3] == b'\xff\xd8\xff': return 'jpg'
        if h[:4] == b'%PDF': return 'pdf'
        if h[:2] == b'PK': return 'zip'
        if h[:4] == b'ftyp': return 'mp4'
        return None

    def _clean_url(self, url):
        url = url.strip().strip('"').strip("'")
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url

    def _get_cookie_file(self):
        cookie_path = os.path.join(os.path.dirname(__file__), "cookies.txt")
        return cookie_path if os.path.exists(cookie_path) else None

    def download_video(self, url, quality="best"):
        url = self._clean_url(url)
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*55}")
        print(f"  🎬 VIDEO DOWNLOAD")
        print(f"{'='*55}{Colors.RESET}")
        print(f"{Colors.WHITE}  URL: {Colors.YELLOW}{url}{Colors.RESET}")
        print(f"{Colors.WHITE}  Quality: {Colors.GREEN}{quality}{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*55}{Colors.RESET}")

        result = self._prenivapi_download(url)
        if result:
            return result

        print_info("Trying direct download...")
        result = self._direct_video_download(url)
        if result:
            return result

        result = self._scrape_og_media(url)
        if result:
            return result

        self._show_supported_platforms()
        return None

    def _show_supported_platforms(self):
        print(f"\n{Colors.BOLD}{Colors.YELLOW}  Supported Platforms:{Colors.RESET}")
        print(f"  {Colors.CYAN}YouTube, Instagram, TikTok, Twitter/X, Facebook{Colors.RESET}")
        print(f"  {Colors.CYAN}Threads, Pinterest, Spotify, Douyin, Bluesky{Colors.RESET}")
        print(f"  {Colors.CYAN}CapCut, RedNote, Kuaishou, Weibo, Apple Music{Colors.RESET}")

    def _prenivapi_download(self, url):
        api_endpoints = {
            'tiktok.com': 'tiktok', 'vm.tiktok.com': 'tiktok',
            'facebook.com': 'facebookv1', 'fb.watch': 'facebookv1', 'fb.com': 'facebookv1',
            'instagram.com': 'igdl', 'instagr.am': 'igdl',
            'twitter.com': 'twitter', 'x.com': 'twitter', 't.co': 'twitter',
            'youtube.com': 'youtube', 'youtu.be': 'youtube',
            'threads.com': 'threads', 'threads.net': 'threads',
            'pinterest.com': 'pinterest', 'pin.it': 'pinterest',
            'douyin.com': 'douyin',
            'spotify.com': 'spotify',
            'music.apple.com': 'applemusic',
            'capcut.com': 'capcut', 'capcut.net': 'capcut',
            'bluesky.com': 'bluesky', 'bsky.app': 'bluesky',
            'xiaohongshu.com': 'rednote', 'rednote.com': 'rednote',
            'kuaishou.com': 'kuaishou',
            'weibo.com': 'weibo',
        }

        detected = None
        for domain, api_name in api_endpoints.items():
            if domain in url.lower():
                detected = api_name
                break

        if not detected:
            return None

        try:
            loading_animation(f"Fetching from {detected} API", 2)
            api_url = f"https://prenivapi.vercel.app/api/{detected}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36'
            }
            r = self.session.get(api_url, params={'url': url}, headers=headers, timeout=25)

            if r.status_code != 200:
                print_warning(f"API returned {r.status_code}")
                return None

            data = r.json()
            if not data.get('status'):
                print_warning(f"API error: {data.get('msg', 'unknown')}")
                return None

            media_data = data.get('data', {})

            download_url = (media_data.get('url') or
                            media_data.get('download'))

            if not download_url and 'downloads' in media_data:
                dl = media_data['downloads']
                if isinstance(dl, dict):
                    for key in ['video', 'audio']:
                        items = dl.get(key, [])
                        if items and isinstance(items, list) and len(items) > 0:
                            download_url = items[0].get('url')
                            if download_url:
                                break

            if not download_url:
                print_warning("No download URL in API response")
                return None

            print_success(f"Found media via API!")
            return self.download_file(download_url)

        except Exception as e:
            print_warning(f"API failed: {e}")
            return None

    def _direct_video_download(self, url):
        try:
            loading_animation("Trying direct download", 1.5)
            html = self.fetch_text(url)
            if not html:
                return None

            patterns = [
                r'https?://[^\s"\'<>]+\.(mp4|webm|mkv|avi|mov)[^\s"\'<>]*',
                r'"(https?://[^"]*\.(mp4|webm|mkv)[^"]*)"',
                r"'(https?://[^']*\.(mp4|webm|mkv)[^']*)'",
                r'data-url\s*=\s*["\'](https?://[^"\']+)["\']',
                r'data-video\s*=\s*["\'](https?://[^"\']+)["\']',
                r'<video[^>]+src\s*=\s*["\']([^"\']+)["\']',
                r'<source[^>]+src\s*=\s*["\']([^"\']+)["\']',
            ]

            all_matches = []
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for m in matches:
                    m = m[0] if isinstance(m, tuple) else m
                    if m.startswith(('http://', 'https://')):
                        all_matches.append(m)

            if all_matches:
                priority_domains = ['googlevideo', 'fbcdn', 'cdninstagram', 'twimg',
                                    'v.redd.it', 'tiktokcdn', 'video', 'media']
                best = all_matches[0]
                for m in all_matches:
                    if any(d in m for d in priority_domains):
                        best = m
                        break
                print_success("Direct video link found!")
                return self.download_file(best)

            json_patterns = [
                r'"video_url"\s*:\s*"([^"]+)"',
                r'"videoUrl"\s*:\s*"([^"]+)"',
                r'"download_url"\s*:\s*"([^"]+)"',
                r'"contentUrl"\s*:\s*"([^"]+)"',
                r'"url"\s*:\s*"([^"]+\.(mp4|webm|mkv))"',
            ]
            for pattern in json_patterns:
                matches = re.findall(pattern, html)
                if matches:
                    m = matches[0] if isinstance(matches[0], str) else matches[0][0]
                    if m.startswith(('http://', 'https://')):
                        print_success("Found video URL in page data!")
                        final = m.replace('\\/', '/').replace('\\u0026', '&')
                        return self.download_file(final)

        except Exception as e:
            print_error(f"Direct download failed: {e}")
        return None

    def _web_fallback_download(self, url):
        platforms = {
            'instagram.com': ['instagram', 'Instagram'],
            'tiktok.com': ['tiktok', 'TikTok'],
            'vm.tiktok.com': ['tiktok', 'TikTok'],
            'facebook.com': ['facebook', 'Facebook'],
            'fb.watch': ['facebook', 'Facebook'],
            'twitter.com': ['twitter', 'Twitter'],
            'x.com': ['twitter', 'Twitter'],
            'youtube.com': ['youtube', 'YouTube'],
            'youtu.be': ['youtube', 'YouTube'],
            'pinterest.com': ['pinterest', 'Pinterest'],
            'pin.it': ['pinterest', 'Pinterest'],
            'reddit.com': ['reddit', 'Reddit'],
            'redd.it': ['reddit', 'Reddit'],
            'linkedin.com': ['linkedin', 'LinkedIn'],
            'snapchat.com': ['snapchat', 'Snapchat'],
            'likee.com': ['likee', 'Likee'],
            'dailymotion.com': ['dailymotion', 'DailyMotion'],
            'dai.ly': ['dailymotion', 'DailyMotion'],
            'vimeo.com': ['vimeo', 'Vimeo'],
            'twitch.tv': ['twitch', 'Twitch'],
            'rumble.com': ['rumble', 'Rumble'],
            't.co': ['twitter', 'Twitter'],
            'threads.net': ['threads', 'Threads'],
            'threads.com': ['threads', 'Threads'],
        }

        detected = None
        for domain, info in platforms.items():
            if domain in url.lower():
                detected = info
                break

        if detected:
            name = detected[1]
            print_info(f"Detected platform: {name}")
            loading_animation(f"Trying {name} fallback", 2)

            if name == 'Threads':
                result = self._threads_download(url)
                if result:
                    return result

            cmd = [
                "yt-dlp", "--no-check-certificates", "--no-warnings",
                "--ignore-errors", "--force-ipv4",
                "-f", "best", "-o", os.path.join(self.download_dir, "%(title).70s.%(ext)s"),
                "--no-overwrites", "--print", "after_move:filepath", url
            ]
            try:
                cookie = self._get_cookie_file()
                if cookie:
                    cmd.extend(["--cookies", cookie])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    filepath = result.stdout.strip().split('\n')[-1]
                    if filepath and os.path.exists(filepath):
                        print_success(f"Downloaded: {filepath}")
                        return filepath
                else:
                    print_warning(f"Fallback failed: {(result.stderr or '')[:100]}")
            except Exception as e:
                print_warning(f"Fallback error: {e}")

            result = self._scrape_og_media(url)
            if result:
                return result

        print_info(f"No download method worked for this URL")
        return None

    def _scrape_og_media(self, url):
        try:
            loading_animation("Scraping page for media", 2)
            html = self.fetch_text(url)
            if not html:
                return None

            og_urls = re.findall(
                r'<meta[^>]*property=[\"\'](?:og:video|og:image|twitter:player|twitter:image)[\"\'][^>]*'
                r'content=[\"\']([^\"\']+)[\"\']',
                html, re.IGNORECASE
            )
            for u in og_urls:
                u = u.replace('&amp;', '&')
                if u.startswith(('http://', 'https://')):
                    print_success(f"Found media in page meta!")
                    return self.download_file(u)

            json_ld = re.findall(
                r'<script[^>]*type=[\"\']application/ld\+json[\"\'][^>]*>(.*?)</script>',
                html, re.DOTALL
            )
            for j in json_ld:
                try:
                    data = json.loads(j)
                    for key in ['contentUrl', 'video', 'image']:
                        val = data.get(key)
                        if isinstance(val, str) and val.startswith(('http://', 'https://')):
                            print_success("Found media in JSON-LD!")
                            return self.download_file(val)
                        if isinstance(val, dict):
                            u = val.get('url', '')
                            if u.startswith(('http://', 'https://')):
                                return self.download_file(u)
                except:
                    pass
        except Exception as e:
            print_warning(f"Scrape failed: {e}")
        return None

    def _threads_download(self, url):
        try:
            loading_animation("Extracting Threads media via API", 3)
            api_url = "https://prenivapi.vercel.app/api/threads"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36'
            }
            r = requests.get(api_url, params={'url': url}, headers=headers, timeout=20)
            if r.status_code != 200:
                print_warning(f"Threads API error: {r.status_code}")
                return None

            data = r.json()
            if not data.get('status') or 'data' not in data:
                print_warning("Threads API returned no data")
                return None

            media_url = data['data'].get('url')
            if not media_url:
                print_warning("No media URL found in Threads API response")
                return None

            media_type = data['data'].get('type', 'video')
            print_success(f"Found {media_type} via Threads API!")
            return self.download_file(media_url)

        except Exception as e:
            print_warning(f"Threads API error: {e}")
        return None

    def download_file(self, url, filename=None):
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        print(f"\n{Colors.BLUE}📥 Downloading: {Colors.YELLOW}{url[:80]}...{Colors.RESET}")
        try:
            resp = self.session.get(url, stream=True, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            print_error(f"Failed: {e}")
            return None

        content_type = resp.headers.get('Content-Type', '')
        chunks = []
        total = int(resp.headers.get('content-length', 0))
        downloaded = 0

        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                chunks.append(chunk)
                downloaded += len(chunk)
                if total:
                    progress_bar(downloaded, total)

        data = b''.join(chunks)
        if not data:
            print_error("Empty response!")
            return None

        ext = self.auto_detect(url, data, resp.headers)
        if not filename:
            cd = resp.headers.get('Content-Disposition', '')
            filename = self._make_filename(url, cd, ext)

        filepath = os.path.join(self.download_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(data)

        size = len(data)
        if size > 1024*1024: sz = f"{size/(1024*1024):.1f} MB"
        elif size > 1024: sz = f"{size/1024:.1f} KB"
        else: sz = f"{size} B"
        print_success(f"Saved: {filepath} ({sz})")
        return filepath

    def _make_filename(self, url, content_disp, ext):
        if content_disp:
            match = re.search(r'filename[*]?=["\']?([^"\';\s]+)', content_disp)
            if match:
                name = re.sub(r'[<>:"/\\|?*]', '_', unquote(match.group(1)))
                if '.' not in name: name = f"{name}.{ext}"
                return name
        path = urlparse(url).path
        name = os.path.basename(unquote(path)).split('?')[0]
        if name and '.' in name:
            name = f"{name.rsplit('.',1)[0]}.{ext}"
        else:
            name = f"file_{int(time.time())}.{ext}"
        return re.sub(r'[<>:"/\\|?*]', '_', name)

    def fetch_text(self, url, delay=0):
        try:
            time.sleep(delay)
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print_error(f"Error: {e}")
            return None

    def parse(self, html):
        return BeautifulSoup(html, 'html.parser')

    def web_search(self, query, num=10):
        loading_animation("Searching DuckDuckGo", 1.5)
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        try:
            resp = self.session.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = []
            for r in soup.select('div.result'):
                title_el = r.select_one('a.result__a')
                desc_el = r.select_one('a.result__snippet')
                if title_el:
                    results.append({
                        'title': title_el.get_text(strip=True),
                        'url': title_el.get('href', ''),
                        'description': desc_el.get_text(strip=True) if desc_el else ''
                    })
            return results[:num]
        except: return []

    def extract_text(self, soup, sel):
        return [el.get_text(strip=True) for el in soup.select(sel)]

    def extract_links(self, soup, sel):
        return [{'text': el.get_text(strip=True), 'url': el.get('href', '')} for el in soup.select(sel)]

    def extract_images(self, soup, sel):
        return [{'src': img.get('src', ''), 'alt': img.get('alt', '')} for img in soup.select(sel)]

    def search_links(self, url, keyword):
        loading_animation("Searching website", 1)
        html = self.fetch_text(url)
        if not html: return []
        soup = self.parse(html)
        results = []
        kw = keyword.lower()
        base_url = url.rstrip('/')
        for a in soup.find_all('a', href=True):
            text = a.get_text(strip=True)
            href = a['href']
            full = href if href.startswith(('http://', 'https://')) else base_url + '/' + href.lstrip('/')
            if kw in text.lower() or kw in href.lower():
                results.append({'text': text, 'url': full})
        return results

    def download_all_images(self, url, selector='img'):
        loading_animation("Fetching page", 1)
        html = self.fetch_text(url)
        if not html: return []
        soup = self.parse(html)
        images = self.extract_images(soup, selector)
        downloaded = []
        for i, img in enumerate(images, 1):
            src = img['src']
            if not src.startswith(('http://', 'https://')):
                src = url.rstrip('/') + '/' + src.lstrip('/')
            print(f"\n{Colors.BLUE}[{i}/{len(images)}]{Colors.RESET} Downloading image...")
            result = self.download_file(src)
            if result: downloaded.append(result)
        print_success(f"{len(downloaded)} images downloaded!")
        return downloaded


def main():
    s = WebScraper()

    print_ascii_art()
    time.sleep(0.5)
    print_banner()

    while True:
        print_menu()
        try:
            choice = input(f"\n{Colors.YELLOW}    Select (1-10): {Colors.RESET}").strip()
        except EOFError:
            print(f"\n{Colors.RED}{Colors.BOLD}    ❌ Input error! Exiting...{Colors.RESET}")
            break

        if choice == '10':
            print(f"\n{Colors.BOLD}{Colors.CYAN}    ╔══════════════════════════════════╗")
            print(f"    ║        👋 Goodbye!               ║")
            print(f"    ║    See you next time!            ║")
            print(f"    ╚══════════════════════════════════╝{Colors.RESET}\n")
            break

        if choice == '1':
            print(f"\n{Colors.BOLD}{Colors.GREEN}    🔍 WEB SEARCH{Colors.RESET}")
            query = input(f"    {Colors.WHITE}Search: {Colors.RESET}").strip()
            if not query: continue
            results = s.web_search(query)
            if not results:
                print_error("Kuch nahi mila!")
                continue
            print(f"\n{Colors.BOLD}{Colors.CYAN}    {'='*50}")
            print(f"    📋 {len(results)} Results: \"{query}\"")
            print(f"    {'='*50}{Colors.RESET}")
            for i, r in enumerate(results, 1):
                if 'title' not in r: continue
                print(f"\n    {Colors.GREEN}{Colors.BOLD}{i}.{Colors.RESET} {Colors.WHITE}{r['title']}{Colors.RESET}")
                print(f"       {Colors.BLUE}{r['url']}{Colors.RESET}")
                if r['description']:
                    print(f"       {Colors.YELLOW}{r['description'][:150]}{Colors.RESET}")

            dl = input(f"\n    {Colors.YELLOW}Video download? (number/no): {Colors.RESET}").strip()
            if dl.isdigit() and 1 <= int(dl) <= len(results):
                s.download_video(results[int(dl)-1].get('url',''))

        elif choice == '2':
            print(f"\n{Colors.BOLD}{Colors.GREEN}    🔎 WEBSITE KEYWORD SEARCH{Colors.RESET}")
            url = input(f"    {Colors.WHITE}URL: {Colors.RESET}").strip()
            if not url.startswith(('http://', 'https://')): url = 'https://' + url
            kw = input(f"    {Colors.WHITE}Keyword: {Colors.RESET}").strip()
            if not kw: continue
            results = s.search_links(url, kw)
            if not results:
                print_error("Kuch nahi mila!")
                continue
            print(f"\n{Colors.BOLD}{Colors.CYAN}    📋 {len(results)} Links Found:{Colors.RESET}")
            for i, r in enumerate(results, 1):
                print(f"    {Colors.GREEN}{i}.{Colors.RESET} {r['text'][:60]} -> {Colors.BLUE}{r['url'][:100]}{Colors.RESET}")
            dl = input(f"\n    {Colors.YELLOW}Download? (number/no): {Colors.RESET}").strip()
            if dl.isdigit() and 1 <= int(dl) <= len(results):
                s.download_video(results[int(dl)-1]['url'])

        elif choice == '3':
            print(f"\n{Colors.BOLD}{Colors.GREEN}    🔗 WEBSITE LINK SEARCH{Colors.RESET}")
            url = input(f"    {Colors.WHITE}URL: {Colors.RESET}").strip()
            if not url.startswith(('http://', 'https://')): url = 'https://' + url
            kw = input(f"    {Colors.WHITE}Keyword: {Colors.RESET}").strip()
            if not kw: continue
            for i, r in enumerate(s.search_links(url, kw), 1):
                print(f"    {Colors.GREEN}{i}.{Colors.RESET} {r['text'][:60]} -> {Colors.BLUE}{r['url'][:100]}{Colors.RESET}")

        elif choice in ['4','5','6']:
            url = input(f"    {Colors.WHITE}URL: {Colors.RESET}").strip()
            if not url.startswith(('http://', 'https://')): url = 'https://' + url
            loading_animation("Fetching page", 1.5)
            html = s.fetch_text(url)
            if not html:
                print_error("Failed!")
                continue
            soup = s.parse(html)
            print_success("Page loaded!")

            if choice == '4':
                sel = input(f"    {Colors.WHITE}CSS selector: {Colors.RESET}").strip()
                data = s.extract_text(soup, sel)
                print(f"\n{Colors.BOLD}{Colors.CYAN}    📋 {len(data)} Elements:{Colors.RESET}")
                for i, t in enumerate(data[:15], 1):
                    print(f"    {Colors.GREEN}{i}.{Colors.RESET} {t[:120]}")
            elif choice == '5':
                sel = input(f"    {Colors.WHITE}CSS selector: {Colors.RESET}").strip()
                data = s.extract_links(soup, sel)
                print(f"\n{Colors.BOLD}{Colors.CYAN}    📋 {len(data)} Links:{Colors.RESET}")
                for i, l in enumerate(data[:15], 1):
                    print(f"    {Colors.GREEN}{i}.{Colors.RESET} {l['text'][:60]} -> {Colors.BLUE}{l['url'][:100]}{Colors.RESET}")
            elif choice == '6':
                sel = input(f"    {Colors.WHITE}Selector (default: img): {Colors.RESET}").strip() or 'img'
                data = s.extract_images(soup, sel)
                print(f"\n{Colors.BOLD}{Colors.CYAN}    🖼️  {len(data)} Images:{Colors.RESET}")
                for i, img in enumerate(data[:15], 1):
                    print(f"    {Colors.GREEN}{i}.{Colors.RESET} {img['alt'][:40]} -> {Colors.BLUE}{img['src'][:100]}{Colors.RESET}")
                if input(f"\n    {Colors.YELLOW}Download all? (y/n): {Colors.RESET}").strip().lower() == 'y':
                    s.download_all_images(url, sel)

        elif choice == '7':
            print(f"\n{Colors.BOLD}{Colors.GREEN}    🎬 VIDEO DOWNLOAD{Colors.RESET}")
            print(f"    {Colors.CYAN}Instagram | TikTok | YouTube | Twitter/X | Facebook{Colors.RESET}")
            print(f"    {Colors.CYAN}Threads | Pinterest | Reddit | LinkedIn | Snapchat{Colors.RESET}")
            print(f"    {Colors.CYAN}Likee | DailyMotion | Vimeo | Twitch | Rumble{Colors.RESET}")
            print(f"    {Colors.CYAN}{'-'*50}{Colors.RESET}")
            url = input(f"    {Colors.WHITE}Paste video link: {Colors.RESET}").strip()
            if not url: continue

            print(f"\n    {Colors.YELLOW}Quality choose karo:{Colors.RESET}")
            print(f"    {Colors.GREEN}1.{Colors.WHITE} Best (original quality)")
            print(f"    {Colors.GREEN}2.{Colors.WHITE} 720p (HD)")
            print(f"    {Colors.GREEN}3.{Colors.WHITE} 480p (SD)")
            print(f"    {Colors.GREEN}4.{Colors.WHITE} 360p (Low)")
            q = input(f"    {Colors.YELLOW}Select (1-4, default=1): {Colors.RESET}").strip()

            quality_map = {'1': 'best', '2': '720', '3': '480', '4': '360'}
            quality = quality_map.get(q, 'best')
            s.download_video(url, quality)

        elif choice == '8':
            print(f"\n{Colors.BOLD}{Colors.GREEN}    📥 FILE DOWNLOAD{Colors.RESET}")
            url = input(f"    {Colors.WHITE}URL: {Colors.RESET}").strip()
            s.download_file(url)

        elif choice == '9':
            print(f"\n{Colors.BOLD}{Colors.GREEN}    🖼️  DOWNLOAD ALL IMAGES{Colors.RESET}")
            url = input(f"    {Colors.WHITE}URL: {Colors.RESET}").strip()
            if not url.startswith(('http://', 'https://')): url = 'https://' + url
            s.download_all_images(url)


if __name__ == "__main__":
    main()
