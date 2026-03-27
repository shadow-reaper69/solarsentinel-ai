/**
 * SolarSentinel AI — Frontend Logic
 * Handles upload, API calls, dashboard rendering, and interactions
 */

(function () {
    'use strict';

    // ── DOM Elements ──
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const previewArea = document.getElementById('previewArea');
    const previewGrid = document.getElementById('previewGrid');
    const imageCount = document.getElementById('imageCount');
    const clearBtn = document.getElementById('clearBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    const loadingBar = document.getElementById('loadingBar');
    const dashboardSection = document.getElementById('dashboardSection');
    const resultsSection = document.getElementById('resultsSection');
    const tableSection = document.getElementById('tableSection');
    const downloadSection = document.getElementById('downloadSection');
    const systemStatus = document.getElementById('systemStatus');

    let selectedFiles = [];
    const MAX_FILES = 20;

    // ── File Upload Handling ──
    browseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFiles(Array.from(e.dataTransfer.files));
    });

    fileInput.addEventListener('change', () => {
        handleFiles(Array.from(fileInput.files));
        fileInput.value = '';
    });

    clearBtn.addEventListener('click', clearFiles);

    function handleFiles(files) {
        const imageFiles = files.filter(f => f.type.startsWith('image/'));
        const remaining = MAX_FILES - selectedFiles.length;

        if (remaining <= 0) {
            alert(`Maximum ${MAX_FILES} images allowed.`);
            return;
        }

        const toAdd = imageFiles.slice(0, remaining);
        selectedFiles.push(...toAdd);
        renderPreviews();
    }

    function clearFiles() {
        selectedFiles = [];
        renderPreviews();
    }

    function removeFile(index) {
        selectedFiles.splice(index, 1);
        renderPreviews();
    }

    function renderPreviews() {
        if (selectedFiles.length === 0) {
            previewArea.style.display = 'none';
            dropZone.style.display = 'block';
            return;
        }

        previewArea.style.display = 'block';
        dropZone.style.display = 'none';
        imageCount.textContent = selectedFiles.length;

        previewGrid.innerHTML = '';
        selectedFiles.forEach((file, idx) => {
            const thumb = document.createElement('div');
            thumb.className = 'preview-thumb';

            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            img.alt = file.name;

            const removeBtn = document.createElement('button');
            removeBtn.className = 'thumb-remove';
            removeBtn.textContent = '×';
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                removeFile(idx);
            });

            const nameSpan = document.createElement('span');
            nameSpan.className = 'thumb-name';
            nameSpan.textContent = file.name;

            thumb.appendChild(img);
            thumb.appendChild(removeBtn);
            thumb.appendChild(nameSpan);
            previewGrid.appendChild(thumb);
        });
    }

    // ── Analyze Images ──
    analyzeBtn.addEventListener('click', analyzeImages);

    async function analyzeImages() {
        if (selectedFiles.length === 0) return;

        // Show loading
        loadingOverlay.style.display = 'flex';
        loadingText.textContent = `Processing ${selectedFiles.length} image${selectedFiles.length > 1 ? 's' : ''}...`;
        loadingBar.style.width = '10%';
        setStatus('analyzing', 'Analyzing...');

        // Hide previous results
        dashboardSection.style.display = 'none';
        resultsSection.style.display = 'none';
        tableSection.style.display = 'none';
        downloadSection.style.display = 'none';

        const formData = new FormData();
        selectedFiles.forEach(file => formData.append('images', file));

        // Simulate progress
        let progress = 10;
        const progressInterval = setInterval(() => {
            progress = Math.min(progress + Math.random() * 8, 90);
            loadingBar.style.width = progress + '%';
        }, 400);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            clearInterval(progressInterval);
            loadingBar.style.width = '100%';

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Upload failed');
            }

            const data = await response.json();

            // Small delay for smooth transition
            await new Promise(r => setTimeout(r, 500));
            loadingOverlay.style.display = 'none';

            // Render results
            renderDashboard(data.summary);
            renderImageResults(data.results);
            renderFaultTable(data.results);

            // Show sections
            dashboardSection.style.display = 'block';
            resultsSection.style.display = 'block';
            tableSection.style.display = 'block';
            downloadSection.style.display = 'block';

            // Scroll to dashboard
            dashboardSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

            setStatus('ready', 'Analysis Complete');

        } catch (error) {
            clearInterval(progressInterval);
            loadingOverlay.style.display = 'none';
            alert('Analysis failed: ' + error.message);
            setStatus('ready', 'System Ready');
        }
    }

    function setStatus(type, text) {
        const dot = systemStatus.querySelector('.status-dot');
        const label = systemStatus.querySelector('span:last-child');
        dot.className = 'status-dot ' + (type === 'analyzing' ? 'status-analyzing' : 'status-ready');
        label.textContent = text;
    }

    // ── Render Dashboard Summary ──
    function renderDashboard(summary) {
        document.getElementById('totalImages').textContent = summary.total_images;
        document.getElementById('totalFaults').textContent = summary.total_faults;
        document.getElementById('hotspotCount').textContent = summary.hotspot_count + (summary.overheating_count || 0);
        document.getElementById('crackCount').textContent = summary.crack_count;
        document.getElementById('dustCount').textContent = summary.dust_count;
        document.getElementById('shadowCount').textContent = summary.shadow_count;
        document.getElementById('healthScore').textContent = summary.health_score;

        const riskEl = document.getElementById('riskLevel');
        riskEl.textContent = summary.risk_level.label;
        riskEl.style.color = summary.risk_level.color;

        const riskWrap = document.getElementById('riskIconWrap');
        riskWrap.style.background = summary.risk_level.color + '20';
        riskWrap.style.color = summary.risk_level.color;

        // Severity breakdown
        const sev = summary.severity_breakdown;
        const total = sev.High + sev.Medium + sev.Low;
        document.getElementById('highCount').textContent = sev.High;
        document.getElementById('mediumCount').textContent = sev.Medium;
        document.getElementById('lowCount').textContent = sev.Low;

        if (total > 0) {
            document.getElementById('segHigh').style.width = (sev.High / total * 100) + '%';
            document.getElementById('segMedium').style.width = (sev.Medium / total * 100) + '%';
            document.getElementById('segLow').style.width = (sev.Low / total * 100) + '%';
        }
    }

    // ── Render Image Results ──
    function renderImageResults(results) {
        const container = document.getElementById('imageResults');
        container.innerHTML = '';

        results.forEach((result, idx) => {
            const card = document.createElement('div');
            card.className = 'image-result-card animate-in';
            card.style.animationDelay = (idx * 0.1) + 's';

            const isError = !!result.error;

            // Header
            let headerHTML = `
                <div class="result-card-header">
                    <span class="result-card-title">📷 ${escHtml(result.filename)}</span>
                    ${!isError ? `<span class="result-card-badge ${result.image_type === 'Thermal' ? 'badge-thermal' : 'badge-normal'}">
                        ${result.image_type === 'Thermal' ? '🌡️' : '📸'} ${result.image_type}
                    </span>` : ''}
                </div>
            `;

            if (isError) {
                card.innerHTML = headerHTML + `
                    <div class="result-card-body">
                        <p style="color: var(--color-danger); font-weight: 600;">⚠️ ${escHtml(result.error)}</p>
                    </div>
                `;
                container.appendChild(card);
                return;
            }

            // Body
            let bodyHTML = '<div class="result-card-body">';

            // Image Row: original vs marked
            bodyHTML += `
                <div class="result-row">
                    <div>
                        <div class="result-image-wrap">
                            <img src="${result.marked_url}" alt="Marked image" loading="lazy">
                            <div class="result-image-label">Detected Faults (${result.fault_count} found)</div>
                        </div>
                    </div>
                    <div>
                        <div class="metadata-panel">
                            <h4>📋 Metadata</h4>
                            ${renderMetadata(result.metadata)}
                        </div>
                        ${renderGPS(result.metadata)}
                    </div>
                </div>
            `;

            // Zoomed Fault Gallery
            const faultsWithZoom = result.faults.filter(f => f.zoom_url);
            if (faultsWithZoom.length > 0) {
                bodyHTML += `
                    <div class="zoom-gallery">
                        <h4>🔍 Zoomed Fault Views</h4>
                        <div class="zoom-grid">
                            ${faultsWithZoom.map(f => `
                                <div class="zoom-card">
                                    <img src="${f.zoom_url}" alt="${f.id} zoom" loading="lazy">
                                    <div class="zoom-card-info">
                                        <div class="zoom-fault-id">${f.id}</div>
                                        <div class="zoom-fault-type">${f.type}</div>
                                        <span class="severity-badge severity-${f.severity.toLowerCase()}">${f.severity}</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            // Predictions
            if (result.predictions && result.predictions.length > 0) {
                bodyHTML += `
                    <div class="predictions-panel">
                        <h4>🔮 AI Predictions & Insights</h4>
                        ${result.predictions.map(pred => `
                            <div class="prediction-item pred-${pred.severity.toLowerCase()}">
                                <div class="pred-header">
                                    <span class="pred-icon">${pred.icon}</span>
                                    <span class="pred-fault-id">${pred.fault_id} — ${pred.fault_type}</span>
                                    <span class="severity-badge severity-${pred.severity.toLowerCase()}">${pred.severity}</span>
                                </div>
                                <div class="pred-prediction">${escHtml(pred.prediction)}</div>
                                <div class="pred-problem"><strong>Problem:</strong> ${escHtml(pred.problem)}</div>
                                <div class="pred-details">
                                    <span><strong>Action:</strong> ${escHtml(pred.recommended_action)}</span>
                                    <span><strong>Efficiency Loss:</strong> ${escHtml(pred.estimated_efficiency_loss)}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            bodyHTML += '</div>';

            card.innerHTML = headerHTML + bodyHTML;
            container.appendChild(card);
        });
    }

    function renderMetadata(meta) {
        if (!meta) return '<p>No metadata available</p>';

        const items = [
            ['File Name', meta.filename],
            ['Date Taken', meta.date_taken],
            ['GPS Latitude', meta.gps_latitude],
            ['GPS Longitude', meta.gps_longitude],
            ['Altitude', meta.altitude],
        ];

        return items.map(([label, value]) => `
            <div class="meta-item">
                <span class="meta-label">${label}</span>
                <span class="meta-value">${escHtml(String(value || 'Not available'))}</span>
            </div>
        `).join('');
    }

    function renderGPS(meta) {
        if (!meta || !meta.has_gps) return '';

        const lat = meta.gps_latitude;
        const lon = meta.gps_longitude;
        const mapsUrl = `https://www.google.com/maps?q=${lat},${lon}`;

        return `
            <div class="gps-section">
                <div class="gps-coords">
                    <strong>📍 GPS:</strong> ${lat}, ${lon}
                </div>
                <a href="${mapsUrl}" target="_blank" rel="noopener" class="btn-maps">
                    🗺️ Open in Google Maps
                </a>
            </div>
        `;
    }

    // ── Render Fault Table ──
    function renderFaultTable(results) {
        const tbody = document.getElementById('faultTableBody');
        tbody.innerHTML = '';

        results.forEach(result => {
            if (result.error) return;

            result.faults.forEach(fault => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${fault.id}</strong></td>
                    <td>${escHtml(result.filename)}</td>
                    <td>${fault.type}</td>
                    <td><span class="table-severity table-severity-${fault.severity.toLowerCase()}">${fault.severity}</span></td>
                    <td>${fault.coordinates || 'N/A'}</td>
                    <td>${(fault.confidence * 100).toFixed(1)}%</td>
                `;
                tbody.appendChild(tr);
            });
        });
    }

    // ── PDF Download ──
    document.getElementById('downloadPdfBtn').addEventListener('click', async () => {
        const btn = document.getElementById('downloadPdfBtn');
        const originalText = btn.innerHTML;
        btn.innerHTML = `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg> Generating PDF...`;
        btn.disabled = true;

        try {
            const response = await fetch('/report');
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Report generation failed');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `solar_inspection_report_${Date.now()}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            alert('PDF generation failed: ' + error.message);
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    });

    // ── Utility ──
    function escHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

})();
