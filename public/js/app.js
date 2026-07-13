// Estado e Configurações iniciais
const API_BASE_URL = window.location.origin;
let selectors = [{ key: 'titulo', value: 'h1' }];

// Elementos da DOM
const selectorsContainer = document.getElementById('selectorsContainer');
const addSelectorBtn = document.getElementById('addSelectorBtn');
const scrapeBtn = document.getElementById('scrapeBtn');
const logSection = document.getElementById('logSection');
const loadingIndicator = document.getElementById('loadingIndicator');
const resultsBox = document.getElementById('resultsBox');
const errorBox = document.getElementById('errorBox');
const placeholderResults = document.getElementById('placeholderResults');
const copyBtn = document.getElementById('copyBtn');

// Função para renderizar os seletores dinâmicos
function renderSelectors() {
    selectorsContainer.innerHTML = '';
    selectors.forEach((sel, index) => {
        const div = document.createElement('div');
        div.className = 'flex gap-2 fade-in';
        
        div.innerHTML = `
            <input
                type="text"
                placeholder="nome_campo"
                value="${sel.key}"
                class="w-1/3 bg-gray-700 text-white p-2 rounded-lg border border-gray-600 focus:ring-1 focus:ring-indigo-500"
                oninput="updateSelector(${index}, 'key', this.value)"
            />
            <input
                type="text"
                placeholder=".classe ou #id"
                value="${sel.value}"
                class="flex-grow bg-gray-700 text-white p-2 rounded-lg border border-gray-600 focus:ring-1 focus:ring-indigo-500"
                oninput="updateSelector(${index}, 'value', this.value)"
            />
            <button 
                onclick="removeSelector(${index})"
                class="bg-red-600 hover:bg-red-700 text-white px-3 rounded-lg transition-colors"
            >X</button>
        `;
        selectorsContainer.appendChild(div);
    });
}

window.updateSelector = (index, field, value) => {
    selectors[index][field] = value;
};

window.removeSelector = (index) => {
    selectors.splice(index, 1);
    renderSelectors();
};

addSelectorBtn.addEventListener('click', () => {
    selectors.push({ key: '', value: '' });
    renderSelectors();
});

// Função de Log
function addLog(message) {
    const timestamp = new Date().toLocaleTimeString();
    const p = document.createElement('div');
    p.className = 'fade-in';
    p.textContent = `[${timestamp}] ${message}`;
    
    // Limpa mensagem inicial se existir
    if (logSection.children.length === 1 && logSection.children[0].tagName === 'P') {
        logSection.innerHTML = '';
    }
    
    logSection.appendChild(p);
    logSection.scrollTop = logSection.scrollHeight;
}

// Ação de Scraping
scrapeBtn.addEventListener('click', async () => {
    const url = document.getElementById('urlInput').value;
    const depth = document.getElementById('depthInput').value;
    const format = document.getElementById('formatInput').value;

    if (!url) {
        alert('Por favor, insira uma URL.');
        return;
    }

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

    addLog(`Iniciando scraper para: ${url}`);
    addLog(`Profundidade: ${depth} | Formato: ${format}`);

    const payload = {
        url: url,
        selectors: selectors.reduce((acc, curr) => {
            if(curr.key && curr.value) acc[curr.key] = curr.value;
            return acc;
        }, {}),
        depth: parseInt(depth),
        format: format
    };

    try {
        // Endpoint ajustado para /api/scrape/text
        addLog(`Enviando requisição para ${API_BASE_URL}/api/scrape/text...`);
        const response = await fetch(`${API_BASE_URL}/api/scrape/text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }

        addLog('Requisição bem-sucedida. Processando dados...');
        const data = await response.json();
        
        resultsBox.textContent = JSON.stringify(data, null, 2);
        resultsBox.classList.remove('hidden');
        copyBtn.classList.remove('hidden');
        addLog('Scraping concluído com sucesso!');

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
        scrapeBtn.innerText = 'Iniciar Scraping';
    }
});

// Botão de Copiar
copyBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(resultsBox.textContent);
    copyBtn.innerText = 'Copiado!';
    setTimeout(() => copyBtn.innerText = 'Copiar JSON', 2000);
});

// Inicializa a UI
renderSelectors();
