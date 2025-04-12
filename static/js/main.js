document.addEventListener('DOMContentLoaded', () => {
    const scrapeForm = document.getElementById('scrapeForm');
    const linksContainer = document.getElementById('linksContainer');
    const startDownloadBtn = document.getElementById('startDownloadBtn');
    const continueDownloadBtn = document.getElementById('continueDownloadBtn');
    const statusMessage = document.getElementById('statusMessage');
    
    let scrapedLinks = [];
    let selectedLinks = [];
    let savePath = '';
    let socket = null;
    
    // Initialize WebSocket connection
    function connectWebSocket() {
        // Close any existing connection
        if (socket) {
            socket.close();
        }
        
        // Create WebSocket connection
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        socket = new WebSocket(`${wsProtocol}//${window.location.host}/ws`);
        
        // Connection opened
        socket.addEventListener('open', (event) => {
            console.log('WebSocket connection established');
        });
        
        // Listen for messages
        socket.addEventListener('message', (event) => {
            const data = JSON.parse(event.data);
            handleProgressUpdate(data);
        });
        
        // Connection closed
        socket.addEventListener('close', (event) => {
            console.log('WebSocket connection closed');
            // Attempt to reconnect after a delay
            setTimeout(connectWebSocket, 3000);
        });
        
        // Connection error
        socket.addEventListener('error', (error) => {
            console.error('WebSocket error:', error);
        });
    }
    
    // Initialize WebSocket connection
    connectWebSocket();
    
    // Handle progress updates from WebSocket
    function handleProgressUpdate(data) {
        console.log('Progress update:', data);
        
        switch (data.status) {
            case 'started':
                // Show progress container
                linksContainer.innerHTML = createProgressBar(data.current, data.total);
                break;
                
            case 'processing':
                // Update progress bar
                updateProgressBar(data.current, data.total, data.filename);
                break;
                
            case 'error':
                // Show error message
                showStatusMessage('danger', `Error: ${data.message}`);
                break;
                
            case 'completed':
                // Show completed links
                if (data.links && data.links.length > 0) {
                    scrapedLinks = data.links;
                    startDownloadBtn.disabled = false;
                    displayLinks(scrapedLinks);
                    showStatusMessage('success', `Completed! Found ${data.links.length} links.`);
                } else {
                    linksContainer.innerHTML = '<p class="text-center text-danger">No links found. Try another URL.</p>';
                }
                break;
        }
    }
    
    // Create progress bar HTML
    function createProgressBar(current, total) {
        const percent = (current / total) * 100;
        return `
            <div class="scraping-progress mb-4">
                <div class="d-flex justify-content-between mb-2">
                    <span class="progress-info">Processing: 0/${total}</span>
                    <span class="progress-percentage">0%</span>
                </div>
                <div class="progress" style="height: 20px;">
                    <div 
                        class="progress-bar progress-bar-striped progress-bar-animated" 
                        role="progressbar" 
                        style="width: 0%" 
                        aria-valuenow="0" 
                        aria-valuemin="0" 
                        aria-valuemax="100"
                    ></div>
                </div>
                <p class="mt-2 current-filename text-muted">Initializing...</p>
            </div>
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p>Scraping links, please wait...</p>
            </div>
        `;
    }
    
    // Update progress bar
    function updateProgressBar(current, total, filename) {
        const percent = Math.round((current / total) * 100);
        const progressBar = document.querySelector('.progress-bar');
        const progressInfo = document.querySelector('.progress-info');
        const progressPercentage = document.querySelector('.progress-percentage');
        const currentFilename = document.querySelector('.current-filename');
        
        if (progressBar) {
            progressBar.style.width = `${percent}%`;
            progressBar.setAttribute('aria-valuenow', percent);
        }
        
        if (progressInfo) {
            progressInfo.textContent = `Processing: ${current}/${total}`;
        }
        
        if (progressPercentage) {
            progressPercentage.textContent = `${percent}%`;
        }
        
        if (currentFilename && filename) {
            currentFilename.textContent = `Current file: ${filename}`;
        }
    }
    
    // Handle form submission for scraping links
    scrapeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = document.getElementById('url').value;
        savePath = document.getElementById('savePath').value;
        
        // Validate save path - make sure it ends with a slash
        if (!savePath.endsWith('/') && !savePath.endsWith('\\')) {
            savePath = savePath + '/';
        }
        
        // Show loading state
        linksContainer.innerHTML = `
            <div class="text-center my-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p>Initializing scraper, please wait...</p>
            </div>
        `;
        
        try {
            // Send request to start scraping
            const response = await fetch('/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    save_path: savePath
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to start scraping');
            }
            
            // The actual results will come via WebSocket
        } catch (error) {
            linksContainer.innerHTML = `<p class="text-center text-danger">Error: ${error.message}</p>`;
            console.error('Error:', error);
        }
    });
    
    // Display the scraped links
    function displayLinks(links) {
        if (links.length === 0) {
            linksContainer.innerHTML = '<p class="text-muted text-center">No links found.</p>';
            return;
        }
        
        let html = `
            <div class="mb-3">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="selectAll">
                        <label class="form-check-label" for="selectAll">Select All</label>
                    </div>
                    <span class="badge bg-primary">${links.length} links found</span>
                </div>
            </div>
            <div class="links-list">`;
        
        links.forEach((link, index) => {
            html += `
                <div class="link-item" data-index="${index}">
                    <div class="form-check">
                        <input class="form-check-input link-checkbox" type="checkbox" id="link${index}" data-index="${index}">
                    </div>
                    <div class="filename">${link.filename}</div>
                </div>`;
        });
        
        html += `</div>`;
        linksContainer.innerHTML = html;
        
        // Handle select all checkbox
        const selectAllCheckbox = document.getElementById('selectAll');
        selectAllCheckbox.addEventListener('change', () => {
            const checkboxes = document.querySelectorAll('.link-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = selectAllCheckbox.checked;
                const index = parseInt(checkbox.getAttribute('data-index'));
                const linkItem = document.querySelector(`.link-item[data-index="${index}"]`);
                
                if (selectAllCheckbox.checked) {
                    selectedLinks = [...scrapedLinks];
                    linkItem.classList.add('checked-item');
                } else {
                    selectedLinks = [];
                    linkItem.classList.remove('checked-item');
                }
            });
            
            updateStartButton();
        });
        
        // Add event listeners for link checkboxes
        const checkboxes = document.querySelectorAll('.link-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                const index = parseInt(checkbox.getAttribute('data-index'));
                const linkItem = document.querySelector(`.link-item[data-index="${index}"]`);
                
                if (checkbox.checked) {
                    selectedLinks.push(scrapedLinks[index]);
                    linkItem.classList.add('checked-item');
                } else {
                    selectedLinks = selectedLinks.filter(link => link.filename !== scrapedLinks[index].filename);
                    linkItem.classList.remove('checked-item');
                    
                    // Update select all checkbox
                    selectAllCheckbox.checked = false;
                }
                
                updateStartButton();
            });
        });
    }
    
    // Update the state of the start download button
    function updateStartButton() {
        startDownloadBtn.disabled = selectedLinks.length === 0;
    }
    
    // Handle start download button
    startDownloadBtn.addEventListener('click', async () => {
        if (selectedLinks.length === 0) return;
        
        try {
            startDownloadBtn.disabled = true;
            startDownloadBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                Starting Download...
            `;
            
            const response = await fetch('/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(selectedLinks)
            });
            
            if (!response.ok) {
                throw new Error('Failed to start download');
            }
            
            const data = await response.json();
            showStatusMessage('success', data.message);
            
            startDownloadBtn.innerHTML = 'Start Download';
            startDownloadBtn.disabled = false;
        } catch (error) {
            showStatusMessage('danger', `Error: ${error.message}`);
            startDownloadBtn.innerHTML = 'Start Download';
            startDownloadBtn.disabled = false;
        }
    });
    
    // Handle continue download button
    continueDownloadBtn.addEventListener('click', async () => {
        try {
            continueDownloadBtn.disabled = true;
            continueDownloadBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                Continuing Download...
            `;
            
            const response = await fetch('/continue');
            
            if (!response.ok) {
                throw new Error('Failed to continue download');
            }
            
            showStatusMessage('success', 'Continuing download from DMS');
            
            continueDownloadBtn.innerHTML = 'Continue Download';
            continueDownloadBtn.disabled = false;
        } catch (error) {
            showStatusMessage('danger', `Error: ${error.message}`);
            continueDownloadBtn.innerHTML = 'Continue Download';
            continueDownloadBtn.disabled = false;
        }
    });
    
    // Show status message
    function showStatusMessage(type, message) {
        statusMessage.className = `alert alert-${type}`;
        statusMessage.textContent = message;
        statusMessage.classList.remove('d-none');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            statusMessage.classList.add('d-none');
        }, 5000);
    }
});