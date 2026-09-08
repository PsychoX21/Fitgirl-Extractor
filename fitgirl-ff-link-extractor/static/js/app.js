document.addEventListener('DOMContentLoaded', () => {
    // State
    let currentLinks = [];
    let extractedResults = [];
    let currentSessionId = null;
    let eventSource = null;
    let currentCategory = 'all';

    // DOM Elements
    const urlInput = document.getElementById('urlInput');
    const fetchBtn = document.getElementById('fetchBtn');
    const fetchBtnText = fetchBtn.querySelector('.btn-text');
    const fetchSpinner = fetchBtn.querySelector('.spinner');
    
    const browserSelect = document.getElementById('browserSelect');
    const headlessToggle = document.getElementById('headlessToggle');
    const backendStatus = document.getElementById('backendStatus');
    
    const partsSection = document.getElementById('partsSection');
    const gameTitle = document.getElementById('gameTitle');
    const partsList = document.getElementById('partsList');
    const showingStatBadge = document.getElementById('showingStatBadge');
    const selectedStatBadge = document.getElementById('selectedStatBadge');
    const actionFooterSummary = document.getElementById('actionFooterSummary');
    
    const countAll = document.getElementById('countAll');
    const countMain = document.getElementById('countMain');
    const countSetup = document.getElementById('countSetup');
    const countOptional = document.getElementById('countOptional');
    
    const filterTabs = document.querySelectorAll('.tab-btn');
    const partFilterInput = document.getElementById('partFilterInput');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    
    const selectVisibleBtn = document.getElementById('selectVisibleBtn');
    const deselectVisibleBtn = document.getElementById('deselectVisibleBtn');
    const selectAllBtn = document.getElementById('selectAllBtn');
    const clearAllBtn = document.getElementById('clearAllBtn');
    
    const startExtractBtn = document.getElementById('startExtractBtn');
    const cancelExtractBtn = document.getElementById('cancelExtractBtn');
    
    const progressSection = document.getElementById('progressSection');
    const progressStatusText = document.getElementById('progressStatusText');
    const progressPercent = document.getElementById('progressPercent');
    const progressBarFill = document.getElementById('progressBarFill');
    const consoleOutput = document.getElementById('consoleOutput');
    
    const resultsSection = document.getElementById('resultsSection');
    const resultsTableBody = document.getElementById('resultsTableBody');
    const rawLinksTextArea = document.getElementById('rawLinksTextArea');
    const copyAllBtn = document.getElementById('copyAllBtn');
    const downloadTxtBtn = document.getElementById('downloadTxtBtn');
    const clearResultsBtn = document.getElementById('clearResultsBtn');
    const toastContainer = document.getElementById('toastContainer');

    // Init
    loadBrowsers();

    // Event Listeners
    fetchBtn.addEventListener('click', handleFetchLinks);
    urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleFetchLinks();
    });

    // Sample buttons
    document.querySelectorAll('.sample-tag').forEach(btn => {
        btn.addEventListener('click', () => {
            urlInput.value = btn.getAttribute('data-url');
            handleFetchLinks();
        });
    });

    // Preset Category Tabs
    filterTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            filterTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentCategory = tab.getAttribute('data-category');
            applyFilters();
        });
    });

    // Search and Clear
    partFilterInput.addEventListener('input', () => {
        clearSearchBtn.classList.toggle('hidden', !partFilterInput.value);
        applyFilters();
    });

    clearSearchBtn.addEventListener('click', () => {
        partFilterInput.value = '';
        clearSearchBtn.classList.add('hidden');
        applyFilters();
        partFilterInput.focus();
    });

    // Selection Controls
    selectVisibleBtn.addEventListener('click', () => setVisibleSelection(true));
    deselectVisibleBtn.addEventListener('click', () => setVisibleSelection(false));
    selectAllBtn.addEventListener('click', () => setGlobalSelection(true));
    clearAllBtn.addEventListener('click', () => setGlobalSelection(false));

    // Extraction
    startExtractBtn.addEventListener('click', handleStartExtraction);
    cancelExtractBtn.addEventListener('click', handleCancelExtraction);

    // Export & Clear
    copyAllBtn.addEventListener('click', handleCopyAll);
    downloadTxtBtn.addEventListener('click', handleDownloadTxt);
    clearResultsBtn.addEventListener('click', handleClearResults);

    // Functions
    async function loadBrowsers() {
        try {
            const res = await fetch('/api/browsers');
            if (res.ok) {
                const data = await res.json();
                browserSelect.innerHTML = '';
                for (const [name, info] of Object.entries(data)) {
                    const opt = document.createElement('option');
                    opt.value = name;
                    opt.textContent = name + (info.available ? ' (Detected)' : ' (Not found)');
                    if (!info.available && name !== 'Auto-Detect Browser') {
                        opt.disabled = true;
                    }
                    browserSelect.appendChild(opt);
                }
                backendStatus.textContent = 'Ready';
            }
        } catch (err) {
            console.error('Failed to load browsers', err);
            backendStatus.textContent = 'Backend Connected';
        }
    }

    async function handleFetchLinks() {
        const url = urlInput.value.trim();
        if (!url) {
            showToast('Please enter a valid FitGirl page URL.', 'error');
            return;
        }

        setFetchingState(true);

        try {
            const res = await fetch('/api/fetch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const json = await res.json();
            if (json.success && json.data) {
                renderDiscoveredParts(json.data);
                showToast(`Discovered ${json.data.links.length} parts!`, 'success');
            } else {
                showToast(json.error || 'Failed to fetch page. Check connection or URL.', 'error');
            }
        } catch (err) {
            showToast('Error connecting to backend: ' + err.message, 'error');
        } finally {
            setFetchingState(false);
        }
    }

    function setFetchingState(isFetching) {
        fetchBtn.disabled = isFetching;
        if (isFetching) {
            fetchSpinner.classList.remove('hidden');
            fetchBtnText.textContent = 'Fetching...';
        } else {
            fetchSpinner.classList.add('hidden');
            fetchBtnText.textContent = 'Fetch Links';
        }
    }

    function renderDiscoveredParts(data) {
        currentLinks = data.links || [];
        gameTitle.textContent = data.title || 'FitGirl Repack';
        
        // Update category counts
        const mainCount = currentLinks.filter(l => l.category === 'main').length;
        const setupCount = currentLinks.filter(l => l.category === 'setup').length;
        const optionalCount = currentLinks.filter(l => l.category === 'optional').length;

        countAll.textContent = currentLinks.length;
        countMain.textContent = mainCount;
        countSetup.textContent = setupCount;
        countOptional.textContent = optionalCount;

        // Reset filter
        partFilterInput.value = '';
        clearSearchBtn.classList.add('hidden');
        filterTabs.forEach(t => t.classList.toggle('active', t.getAttribute('data-category') === 'all'));
        currentCategory = 'all';

        partsSection.classList.remove('hidden');
        partsSection.scrollIntoView({ behavior: 'smooth' });

        buildPartsDOM(currentLinks);
        applyFilters();
    }

    function buildPartsDOM(links) {
        partsList.innerHTML = '';

        if (links.length === 0) {
            partsList.innerHTML = '<div class="console-line error" style="padding: 10px;">No fuckingfast.co links found on this page!</div>';
            return;
        }

        links.forEach(link => {
            const item = document.createElement('div');
            item.className = 'part-item' + (link.selected ? ' active' : '');
            item.setAttribute('data-id', link.id);
            item.setAttribute('data-name', link.name.toLowerCase());
            item.setAttribute('data-category', link.category || 'main');

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = link.selected;
            checkbox.id = `part-chk-${link.id}`;

            const details = document.createElement('div');
            details.className = 'part-details';

            const badge = document.createElement('span');
            badge.className = `category-badge category-${link.category || 'main'}`;
            badge.textContent = link.category || 'main';

            const label = document.createElement('span');
            label.className = 'part-name';
            label.textContent = link.name;
            label.title = link.url;

            details.appendChild(badge);
            details.appendChild(label);

            // Toggle on whole item click
            item.addEventListener('click', (e) => {
                if (e.target !== checkbox) {
                    checkbox.checked = !checkbox.checked;
                }
                link.selected = checkbox.checked;
                item.classList.toggle('active', link.selected);
                updateStats();
            });

            item.appendChild(checkbox);
            item.appendChild(details);
            partsList.appendChild(item);
        });
    }

    function applyFilters() {
        const query = partFilterInput.value.trim().toLowerCase();
        const items = partsList.querySelectorAll('.part-item');
        let visibleCount = 0;

        items.forEach(item => {
            const name = item.getAttribute('data-name');
            const category = item.getAttribute('data-category');

            const matchesCategory = (currentCategory === 'all' || category === currentCategory);
            const matchesQuery = (!query || name.includes(query));

            if (matchesCategory && matchesQuery) {
                item.style.display = 'flex';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });

        showingStatBadge.textContent = `Showing ${visibleCount} of ${currentLinks.length}`;
        updateStats();
    }

    function setVisibleSelection(selected) {
        const items = partsList.querySelectorAll('.part-item');
        let affected = 0;

        items.forEach(item => {
            if (item.style.display !== 'none') {
                const id = parseInt(item.getAttribute('data-id'));
                const link = currentLinks.find(l => l.id === id);
                if (link) {
                    link.selected = selected;
                    const chk = item.querySelector('input[type="checkbox"]');
                    if (chk) chk.checked = selected;
                    item.classList.toggle('active', selected);
                    affected++;
                }
            }
        });

        showToast(`${selected ? 'Selected' : 'Deselected'} ${affected} visible parts`, 'info');
        updateStats();
    }

    function setGlobalSelection(selected) {
        currentLinks.forEach(link => link.selected = selected);
        document.querySelectorAll('.part-item').forEach(item => {
            const chk = item.querySelector('input[type="checkbox"]');
            if (chk) chk.checked = selected;
            item.classList.toggle('active', selected);
        });
        showToast(`${selected ? 'Selected' : 'Deselected'} all ${currentLinks.length} parts`, 'info');
        updateStats();
    }

    function updateStats() {
        const total = currentLinks.length;
        const selected = currentLinks.filter(l => l.selected).length;
        
        selectedStatBadge.textContent = `${selected} Selected`;
        actionFooterSummary.textContent = `${selected} of ${total} parts selected for extraction`;
        startExtractBtn.disabled = (selected === 0);
    }

    async function handleStartExtraction() {
        const selectedLinks = currentLinks.filter(l => l.selected);
        if (selectedLinks.length === 0) {
            showToast('Please select at least one part to extract.', 'error');
            return;
        }

        const browser = browserSelect.value;
        const headless = headlessToggle.checked;

        // Reset UI
        extractedResults = [];
        resultsTableBody.innerHTML = '';
        rawLinksTextArea.value = '';
        consoleOutput.innerHTML = '';
        appendLog('info', `Starting stealth extraction job for ${selectedLinks.length} parts...`);

        // Show sections
        progressSection.classList.remove('hidden');
        resultsSection.classList.remove('hidden');
        progressSection.scrollIntoView({ behavior: 'smooth' });

        updateProgress(0, selectedLinks.length, 0, 'Initializing stealth browser...');

        startExtractBtn.classList.add('hidden');
        cancelExtractBtn.classList.remove('hidden');

        try {
            const startRes = await fetch('/api/extract/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    links: selectedLinks,
                    browser: browser,
                    headless: headless
                })
            });

            const startData = await startRes.json();
            if (!startData.success) {
                showToast(startData.error || 'Failed to start extraction.', 'error');
                resetExtractControls();
                return;
            }

            currentSessionId = startData.session_id;
            listenToStream(currentSessionId);

        } catch (err) {
            showToast('Failed to start extraction: ' + err.message, 'error');
            resetExtractControls();
        }
    }

    function listenToStream(sessionId) {
        if (eventSource) {
            eventSource.close();
        }

        eventSource = new EventSource(`/api/extract/stream/${sessionId}`);

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleStreamEvent(data);
            } catch (err) {
                console.error('Error parsing SSE event:', err);
            }
        };

        eventSource.onerror = (err) => {
            console.error('SSE Error:', err);
            // Don't panic if it's just closing on completion
            if (currentSessionId) {
                appendLog('info', 'SSE Stream disconnected or completed.');
            }
        };
    }

    function handleStreamEvent(data) {
        switch (data.type) {
            case 'ping':
                // Keep-alive heartbeat
                break;

            case 'log':
                const logType = data.message.includes('✓') ? 'success' : 
                               (data.message.includes('✗') || data.message.includes('Error')) ? 'error' : 'info';
                appendLog(logType, data.message);
                break;

            case 'progress':
                updateProgress(data.current, data.total, data.percent, `Processing: ${data.current_item}`);
                break;

            case 'item_result':
                handleItemResult(data);
                break;

            case 'done':
                updateProgress(data.total, data.total, 100, `Done! Extracted ${data.successful}/${data.total} direct links.`);
                appendLog('success', `Completed! ${data.successful} successful, ${data.failed} failed.`);
                showToast(`Extraction Complete! (${data.successful}/${data.total} successful)`, 'success');
                resetExtractControls();
                if (eventSource) eventSource.close();
                break;

            case 'error':
                appendLog('error', data.message);
                showToast(data.message, 'error');
                resetExtractControls();
                if (eventSource) eventSource.close();
                break;
        }
    }

    function handleItemResult(result) {
        extractedResults.push(result);

        const row = document.createElement('tr');
        const index = extractedResults.length;

        const tdIndex = `<td>${index}</td>`;
        const tdName = `<td><strong>${escapeHtml(result.name)}</strong></td>`;
        
        let tdLink = '';
        let tdStatus = '';
        let tdAction = '';

        if (result.success && result.direct_url) {
            tdLink = `<td class="direct-link-cell"><a href="${result.direct_url}" target="_blank" rel="noopener noreferrer">${escapeHtml(result.direct_url)}</a></td>`;
            tdStatus = `<td><span class="badge badge-success">Extracted</span></td>`;
            tdAction = `<td><button class="btn btn-secondary btn-sm" onclick="navigator.clipboard.writeText('${result.direct_url}'); alert('Direct link copied!');">Copy</button></td>`;
            
            if (rawLinksTextArea.value) {
                rawLinksTextArea.value += '\n' + result.direct_url;
            } else {
                rawLinksTextArea.value = result.direct_url;
            }
        } else {
            tdLink = `<td class="direct-link-cell" style="color: #f87171;">${escapeHtml(result.error || 'Failed to extract')}</td>`;
            tdStatus = `<td><span class="badge badge-failed">Failed</span></td>`;
            tdAction = `<td><button class="btn btn-secondary btn-sm" onclick="navigator.clipboard.writeText('${result.original_url}'); alert('Original link copied!');">Original</button></td>`;
        }

        row.innerHTML = tdIndex + tdName + tdLink + tdStatus + tdAction;
        resultsTableBody.appendChild(row);
    }

    function updateProgress(current, total, percent, status) {
        progressBarFill.style.width = `${percent}%`;
        progressPercent.textContent = `${percent}% (${current}/${total})`;
        progressStatusText.textContent = status;
    }

    function appendLog(type, message) {
        const line = document.createElement('div');
        line.className = `console-line ${type}`;
        const time = new Date().toLocaleTimeString();
        line.textContent = `[${time}] ${message}`;
        consoleOutput.appendChild(line);
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }

    async function handleCancelExtraction() {
        if (!currentSessionId) return;
        try {
            await fetch(`/api/extract/cancel/${currentSessionId}`, { method: 'POST' });
            showToast('Stopping extraction...', 'error');
            appendLog('info', 'Sent cancellation request...');
        } catch (err) {
            console.error(err);
        }
    }

    function resetExtractControls() {
        startExtractBtn.classList.remove('hidden');
        cancelExtractBtn.classList.add('hidden');
    }

    function handleCopyAll() {
        const text = rawLinksTextArea.value.trim();
        if (!text) {
            showToast('No direct links to copy!', 'error');
            return;
        }

        navigator.clipboard.writeText(text).then(() => {
            showToast('All direct download links copied to clipboard!', 'success');
        }).catch(err => {
            showToast('Failed to copy: ' + err.message, 'error');
        });
    }

    function handleDownloadTxt() {
        const text = rawLinksTextArea.value.trim();
        if (!text) {
            showToast('No direct links to export!', 'error');
            return;
        }

        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        const filename = (gameTitle.textContent.replace(/[^a-z0-9]/gi, '_').toLowerCase() || 'fitgirl_links') + '_direct_links.txt';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast(`Exported ${filename}`, 'success');
    }

    function handleClearResults() {
        extractedResults = [];
        resultsTableBody.innerHTML = '';
        rawLinksTextArea.value = '';
        progressSection.classList.add('hidden');
        resultsSection.classList.add('hidden');
        showToast('Results cleared.', 'success');
    }

    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${type === 'success' ? '✓' : '⚠️'}</span> <span>${escapeHtml(message)}</span>`;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(12px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
});
