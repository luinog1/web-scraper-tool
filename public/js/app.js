// Configurações iniciais
const API_BASE_URL = window.location.origin;

// Elementos da DOM
const operationSelect = document.getElementById('operationSelect');
const dynamicInputs = document.getElementById('dynamicInputs');
const scrapeBtn = document.getElementById('scrapeBtn');
const logSection = document.getElementById('logSection');
const loadingIndicator = document.getElementById('loadingIndicator');
const resultsBox = document.getElementById('resultsBox');
const errorBox = document.getElementById('errorBox');
const placeholderResults = document.getElementById('placeholderResults');
const copyBtn = document.getElementById('copyBtn');

// Mapeamento de operações para endpoints da API
const API_ENDPOINTS = {
    hashtag_search: { method: 'GET', path: '/api/search' },
    web_search: { method: 'GET', path: '/api/search' },
    text_scrape: { method: 'POST', path: '/api/scrape/text' },
    links_scrape: { method: 'POST', path: '/api/scrape/links' },
    images_scrape: { method: 'POST', path: '/api/scrape/images' },
    video_download: { method: 'POST', path: '/api/video' },
    list_downloads: { method: 'GET', path: '/api/downloads' }
};

// Função para renderizar os campos de entrada dinamicamente
function renderInputs(op) {
    let html = '';
    switch(op) {
        case 'hashtag_search':
        case 'web_search':
            html = `
                <div>
                    <label class="block text-sm font-medium text-gray-400 mb-2">Hashtag ou Termo de Busca</label>
                    <input type="text" id="searchQuery" placeholder="Ex: #tecnologia, python, memes" class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:ring-2 focus:ring-indigo-500">
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-400 mb-2">Filtrar por Rede Social</label>
                    <select id="platformFilter" class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:ring-2 focus:ring-indigo-500">
                        <option value="all">🌐 Web (Todos os sites)</option>
                        <option value="tiktok">🎵 TikTok (Extrai vídeos via Apify)</option>
                        <option value="instagram">📸 Instagram (Busca no Google)</option>
                        <option value="youtube">▶️ YouTube (Busca no Google)</option>
                        <option value="twitter">🐦 Twitter/X (Busca no Google)</option>
                        <option value="facebook">👤 Facebook (Busca no Google)</option>
                    </select>
                </div>

                <div>
                    <label class="block text-sm font-medium text-gray-400 mb-2">Ordenar Resultados (Apenas TikTok)</label>
                    <select id="sortBy" class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:ring-2 focus:ring-indigo-500">
                        <option value="relevance">⭐ Relevância (Padrão do TikTok)</option>
                        <option value="views">👀 Maior Número de Visualizações</option>
                        <option value="likes">❤️ Maior Número de Curtidas</option>
                    </select>
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-400 mb-2">Número de Resultados</label>
                    <input type="number" id="searchNum" value="15" min="1" max="50" class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:ring-2 focus:ring-indigo-500">
                </div>
            `;
            break;
        case 'text_scrape':
        case 'links_scrape':
        case 'images_scrape':
            html = `
                <div>
                    <label class="block text-sm font-medium text-gray-400 mb-2">URL Alvo</label>
                    <input type="url" id="targetUrl" placeholder="https://exemplo.com" class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:ring-2 focus:ring-indigo-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-400 mb-2">Seletor CSS (Opcional)</label>
                    <input type="text" id="cssSelector" placeholder="h1, .classe, #id, a, img" class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:ring-2 focus:ring-indigo-500">
                    <p class="text-xs text-gray-500 mt-1">Deixe em branco para usar seletores padrão (p, a, img).</p>
                </div>
            `;
            break;
        case 'video_download':
            html = `
                <div>
                    <label class="block text-sm font-medium text-gray-400 mb-2">URL do Vídeo</label>
                    <input type="url" id="videoUrl" placeholder="https://youtube.com/watch?v=..." class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:ring-2 focus:ring-indigo-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-400 mb-2">Qualidade</label>
                    <select id="videoQuality" class="w-full bg-gray-700 text-white p-3 rounded-lg border border-gray-600 focus:ring-2 focus:ring-indigo-500">
                        <option value="best">Melhor Qualidade (Original)</option>
                        <option value="720">720p (HD)</option>
                        <option value="480">480p (SD)</option>
                        <option value="360">360p (Baixa)</option>
                    </select>
                </div>
                <p class="text-xs text-yellow-500 bg-yellow-900/30 p-2 rounded">Nota: Para TikTok, o sistema usará o Apify automaticamente. Para YouTube/Twitter, usará yt-dlp.</p>
            `;
            break;
        case 'list_downloads':
            html = `<p class="text-gray-400 text-sm bg-gray-700 p-3 rounded-lg">Nenhuma entrada necessária. Clique em Executar para listar os arquivos baixados no servidor.</p>`;
            break;
    }
    dynamicInputs.innerHTML = html;
}

// Função de Log
function addLog(message) {
    const timestamp = new Date().toLocaleTimeString();
    const p = document.createElement('div');
    p.className = 'fade-in';
    p.textContent = `[${timestamp}] ${message}`;
    
    if (logSection.children.length === 1 && logSection.children[0].tagName === 'P') {
        logSection.innerHTML = '';
    }
    
    logSection.appendChild(p);
    logSection.scrollTop = logSection.scrollHeight;
}

// Ação principal ao clicar no botão
scrapeBtn.addEventListener('click', async () => {
    const op = operationSelect.value;
    const config = API_ENDPOINTS[op];
    
    let url = `${API_BASE_URL}${config.path}`;
    let options = {
        method: config.method,
        headers: {}
    };

    // Resetar UI
    loadingIndicator.classList.remove('hidden');
    scrapeBtn.disabled = true;
    scrapeBtn.classList.add('bg-gray-600', 'cursor-not-allowed');
    scrapeBtn.classList.remove('bg-indigo-600', 'hover:bg-indigo-700');
    scrapeBtn.innerText = 'Processando...';
    
    errorBox.classList.add('hidden');
    resultsBox.classList.add('hidden');
    copyBtn.classList.add('hidden');
    placeholderResults.classList.add('hidden');
    logSection.innerHTML = '';

    addLog(`Iniciando operação: ${operationSelect.options[operationSelect.selectedIndex].text}`);

    try {
        if (op === 'hashtag_search' || op === 'web_search') {
            const q = document.getElementById('searchQuery').value;
            const num = document.getElementById('searchNum').value;
            const platform = document.getElementById('platformFilter').value;
            const sort_by = document.getElementById('sortBy').value;
            
            if (!q) throw new Error("Insira um termo de pesquisa.");
            
            url += `?q=${encodeURIComponent(q)}&num=${num}&platform=${platform}&sort_by=${sort_by}`;
            addLog(`Pesquisando por: ${q} (Filtro: ${platform}, Ordenação: ${sort_by})`);
            
        } else if (op === 'text_scrape' || op === 'links_scrape' || op === 'images_scrape') {
            const targetUrl = document.getElementById('targetUrl').value;
            const selector = document.getElementById('cssSelector').value || "p";
            if (!targetUrl) throw new Error("Insira uma URL alvo.");
            
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify({ url: targetUrl, selector: selector });
            addLog(`Scraping URL: ${targetUrl} com seletor: ${selector}`);
            
        } else if (op === 'video_download') {
            const videoUrl = document.getElementById('videoUrl').value;
            const quality = document.getElementById('videoQuality').value;
            if (!videoUrl) throw new Error("Insira uma URL de vídeo.");
            
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify({ url: videoUrl, quality: quality });
            addLog(`Extraindo link de vídeo: ${videoUrl} (${quality})`);
            
        } else if (op === 'list_downloads') {
            addLog('Listando arquivos no diretório de downloads do servidor...');
        }

        addLog(`Enviando requisição ${config.method} para ${config.path}...`);
        const response = await fetch(url, options);

        if (!response.ok) {
            const errData = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(`Erro HTTP ${response.status}: ${errData.detail || 'Falha no servidor'}`);
        }

        const data = await response.json();
        
        resultsBox.textContent = JSON.stringify(data, null, 2);
        resultsBox.classList.remove('hidden');
        copyBtn.classList.remove('hidden');
        addLog('Operação concluída com sucesso!');

    } catch (err) {
        errorBox.innerHTML = `<strong>Erro:</strong> ${err.message}`;
        errorBox.classList.remove('hidden');
        placeholderResults.classList.remove('hidden');
        addLog(`ERRO: ${err.message}`);
    } finally {
        loadingIndicator.classList.add('hidden');
        scrapeBtn.disabled = false;
        scrapeBtn.classList.remove('bg-gray-600', 'cursor-not-allowed');
        scrapeBtn.classList.add('bg-indigo-600', 'hover:bg-indigo-700');
        scrapeBtn.innerText = 'Executar Operação';
    }
});

// Botão de Copiar
copyBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(resultsBox.textContent);
    copyBtn.innerText = 'Copiado!';
    setTimeout(() => copyBtn.innerText = 'Copiar JSON', 2000);
});

// Inicializa a UI
operationSelect.addEventListener('change', (e) => renderInputs(e.target.value));
renderInputs('hashtag_search');
