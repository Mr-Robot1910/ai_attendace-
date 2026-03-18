// ─── Toast ────────────────────────────────────────────────────────────────────
function showToast(message, type = 'info') {
    const svgs = {
        success: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
        error:   `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
        info:    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
    };
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-icon">${svgs[type]}</div>
        <div class="toast-msg">${message}</div>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(60px) scale(0.92)';
        toast.style.transition = '0.35s ease';
    }, 3500);
    setTimeout(() => toast.remove(), 3900);
}

// ─── Theme Toggle ─────────────────────────────────────────────────────────────
function initThemeToggle() {
    const toggleBtn = document.getElementById('themeToggle');
    if (!toggleBtn) return;
    
    const moonIcon = toggleBtn.querySelector('.moon-icon');
    const sunIcon = toggleBtn.querySelector('.sun-icon');
    
    const currentTheme = localStorage.getItem('theme') || 'dark';
    if (currentTheme === 'light') {
        document.body.classList.add('light');
        if (moonIcon) moonIcon.classList.add('hidden');
        if (sunIcon) sunIcon.classList.remove('hidden');
    }

    toggleBtn.addEventListener('click', () => {
        const isLight = document.body.classList.toggle('light');
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
        if (moonIcon) moonIcon.classList.toggle('hidden', isLight);
        if (sunIcon)  sunIcon.classList.toggle('hidden', !isLight);
    });
}

// ─── Mobile Sidebar ───────────────────────────────────────────────────────────
function initMobileSidebar() {
    const toggle  = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (!toggle || !sidebar) return;

    function openSidebar() {
        sidebar.classList.add('open');
        overlay.classList.add('open');
        toggle.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden';
    }
    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
    }

    toggle.addEventListener('click', () => {
        sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
    });
    overlay.addEventListener('click', closeSidebar);

    // Close on ESC
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSidebar(); });
}

// ─── Number Counters ──────────────────────────────────────────────────────────
function initCounters() {
    const counters = document.querySelectorAll('.counter-num');
    counters.forEach(counter => {
        const target = +counter.getAttribute('data-target');
        const duration = 1200;
        const step = target / (duration / 16); 
        
        let current = 0;
        const update = () => {
            current += step;
            if (current < target) {
                counter.innerText = Math.ceil(current);
                requestAnimationFrame(update);
            } else {
                counter.innerText = target;
            }
        };
        if (target > 0) setTimeout(update, 300);
        else counter.innerText = '0';
    });
}

// ─── Notification Panel ───────────────────────────────────────────────────────
function initNotifications() {
    const toggle = document.getElementById('notifToggle');
    const panel  = document.getElementById('notifPanel');
    if (!toggle || !panel) return;

    toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        panel.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
        if (!panel.contains(e.target)) {
            panel.classList.remove('open');
        }
    });
}

// ─── Greeting Banner ──────────────────────────────────────────────────────────
function initGreeting() {
    const el   = document.getElementById('greetingText');
    const sub  = document.getElementById('greetingDate');
    if (!el) return;

    const hour = new Date().getHours();
    const greet = hour < 12 ? 'Good morning 👋' : hour < 17 ? 'Good afternoon 👋' : 'Good evening 👋';
    el.textContent = greet;

    if (sub) {
        const opts = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        sub.textContent = new Date().toLocaleDateString(undefined, opts);
    }
}

// ─── Register Page ────────────────────────────────────────────────────────────
function initRegisterPage() {
    const video       = document.getElementById('videoEl');
    const canvas      = document.getElementById('captureCanvas');
    const captureBtn  = document.getElementById('captureBtn');
    const retakeBtn   = document.getElementById('retakeBtn');
    const registerBtn = document.getElementById('registerBtn');
    const cameraWrap  = document.getElementById('cameraWrap');
    const captureCountLabel = document.getElementById('captureCountLabel');
    if (!video) return;

    let capturedImages = [];
    const MAX_CAPTURES = 5;

    // ── Stepper ──
    function setStep(n) {
        for (let i = 1; i <= 4; i++) {
            const el = document.getElementById('step' + i);
            if (!el) continue;
            const dot   = el.querySelector('div');
            const label = el.querySelector('span');
            if (i < n) {
                if (dot)   { dot.style.background='rgba(0,245,255,0.20)'; dot.style.color='var(--cyan)'; dot.style.borderColor='rgba(0,245,255,0.5)'; }
                if (label) { label.style.color='var(--text-secondary)'; }
            } else if (i === n) {
                if (dot)   { dot.style.background='rgba(0,245,255,0.15)'; dot.style.color='var(--cyan)'; dot.style.borderColor='rgba(0,245,255,0.45)'; dot.style.boxShadow='0 0 14px rgba(0,245,255,0.2)'; }
                if (label) { label.style.color='var(--cyan)'; }
            } else {
                if (dot)   { dot.style.background='rgba(255,255,255,0.05)'; dot.style.color='var(--text-muted)'; dot.style.borderColor='var(--glass-border)'; dot.style.boxShadow='none'; }
                if (label) { label.style.color='var(--text-muted)'; }
            }
        }
    }
    setStep(1);

    // ── Camera ──
    async function startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
            video.srcObject = stream;
            video.play();
            const overlay = document.getElementById('camOverlay');
            if (overlay) overlay.style.display = 'none';
            if (cameraWrap) cameraWrap.classList.add('active');
            setStep(2);
        } catch {
            showToast('Camera access denied. Please allow camera permission.', 'error');
        }
    }
    startCamera();

    // ── Capture ──
    captureBtn.addEventListener('click', async () => {
        if (capturedImages.length >= MAX_CAPTURES) return;
        captureBtn.disabled = true;
        try {
            canvas.width  = video.videoWidth  || 640;
            canvas.height = video.videoHeight || 480;
            canvas.getContext('2d').drawImage(video, 0, 0);
            const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
            capturedImages.push(dataUrl);

            // Update thumbnail
            const thumbIdx = capturedImages.length;
            const thumb = document.getElementById('thumb' + thumbIdx);
            if (thumb) {
                thumb.classList.remove('empty');
                thumb.classList.add('captured');
                thumb.innerHTML = `<img src="${dataUrl}" alt="Capture ${thumbIdx}">`;
            }
            if (captureCountLabel) captureCountLabel.textContent = capturedImages.length;

            // Enable register after first capture
            if (capturedImages.length >= 1) {
                registerBtn.disabled = false;
                registerBtn.removeAttribute('aria-disabled');
                retakeBtn.classList.remove('hidden');
                setStep(3);
            }
            if (capturedImages.length >= MAX_CAPTURES) {
                captureBtn.disabled = true;
                showToast(`All ${MAX_CAPTURES} captures done! Ready to register.`, 'info');
            }
        } finally {
            if (capturedImages.length < MAX_CAPTURES) captureBtn.disabled = false;
        }
    });

    // ── Retake ──
    retakeBtn.addEventListener('click', () => {
        capturedImages = [];
        if (captureCountLabel) captureCountLabel.textContent = 0;
        for (let i = 1; i <= MAX_CAPTURES; i++) {
            const thumb = document.getElementById('thumb' + i);
            if (thumb) { thumb.classList.add('empty'); thumb.classList.remove('captured'); thumb.innerHTML = `<span class="thumb-num">${i}</span>`; }
        }
        retakeBtn.classList.add('hidden');
        registerBtn.disabled = true;
        registerBtn.setAttribute('aria-disabled', 'true');
        captureBtn.disabled = false;
        setStep(2);
    });

    // ── Register ──
    registerBtn.addEventListener('click', async () => {
        const name  = document.getElementById('studentName').value.trim();
        const roll  = document.getElementById('rollNo').value.trim();
        const email = (document.getElementById('studentEmail') || {}).value?.trim() || '';
        if (!name || !roll) { showToast('Please enter name and roll number.', 'error'); return; }
        if (!capturedImages.length) { showToast('Please capture at least one photo.', 'error'); return; }

        const origHtml = registerBtn.innerHTML;
        registerBtn.disabled = true;
        registerBtn.innerHTML = `<div class="spinner"></div> Registering…`;
        try {
            const resp = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, roll_no: roll, email, images: capturedImages })
            });
            const data = await resp.json();
            if (data.success) {
                setStep(4);
                showToast(`✨ ${name} registered! (${data.frames_used || capturedImages.length} frames used)`, 'success');
                document.getElementById('studentName').value = '';
                document.getElementById('rollNo').value = '';
                if (document.getElementById('studentEmail')) document.getElementById('studentEmail').value = '';
                retakeBtn.click(); // Reset thumbnails
                setTimeout(() => setStep(1), 3000);
            } else {
                showToast(data.error || 'Registration failed.', 'error');
                registerBtn.disabled = false;
                registerBtn.innerHTML = origHtml;
            }
        } catch {
            showToast('Network error. Please try again.', 'error');
            registerBtn.disabled = false;
            registerBtn.innerHTML = origHtml;
        }
    });
}

// ─── Attendance Page ──────────────────────────────────────────────────────────
function initAttendancePage() {
    const startBtn        = document.getElementById('startBtn');
    const stopBtn         = document.getElementById('stopBtn');
    const feedImg         = document.getElementById('feedImg');
    const feedPlaceholder = document.getElementById('feedPlaceholder');
    const recognizedList  = document.getElementById('recognizedList');
    const sessionStatus   = document.getElementById('sessionStatus');
    const qualityBanner   = document.getElementById('qualityBanner');
    const qualityIcon     = document.getElementById('qualityIcon');
    const qualityText     = document.getElementById('qualityText');
    const scanLine        = document.getElementById('scanLine');
    const liveCounterNum  = document.getElementById('liveCounterNum');
    let polling = null;
    let recognizedIds = new Set();
    let recognizedCount = 0;

    if (!startBtn) return;
    const cameraWrapEl = document.getElementById('cameraWrap');

    startBtn.addEventListener('click', async () => {
        startBtn.disabled = true;
        startBtn.innerHTML = `<div class="spinner"></div> Starting…`;
        try {
            const resp = await fetch('/api/attendance/start', { method: 'POST' });
            const data = await resp.json();
            if (data.success) {
                feedImg.src = '/api/attendance/feed?' + Date.now();
                feedImg.classList.remove('hidden');
                if (feedPlaceholder) feedPlaceholder.style.display = 'none';
                if (cameraWrapEl) cameraWrapEl.classList.add('active');
                stopBtn.disabled = false;
                startBtn.disabled = true;
                if (sessionStatus) {
                    sessionStatus.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" stroke="none" style="width:8px;height:8px"><circle cx="12" cy="12" r="10"/></svg> Session Active`;
                    sessionStatus.className = 'badge badge-green';
                }
                polling = setInterval(pollStatus, 1500);
            } else {
                showToast(data.error || 'Could not start session.', 'error');
                startBtn.disabled = false;
                startBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg> Start Session`;
            }
        } catch {
            showToast('Failed to start session.', 'error');
            startBtn.disabled = false;
            startBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg> Start Session`;
        }
    });

    stopBtn.addEventListener('click', async () => {
        clearInterval(polling);
        await fetch('/api/attendance/stop', { method: 'POST' });
        feedImg.src = ''; feedImg.classList.add('hidden');
        if (feedPlaceholder) feedPlaceholder.style.display = 'flex';
        if (cameraWrapEl) cameraWrapEl.classList.remove('active');
        stopBtn.disabled = true;
        startBtn.disabled = false;
        startBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg> Start Session`;
        if (sessionStatus) {
            sessionStatus.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" stroke="none" style="width:8px;height:8px"><circle cx="12" cy="12" r="10"/></svg> Session Stopped`;
            sessionStatus.className = 'badge badge-red';
        }
    });

    async function pollStatus() {
        try {
            const [statusResp, qualityResp] = await Promise.all([
                fetch('/api/attendance/status'),
                fetch('/api/attendance/quality')
            ]);
            const data  = await statusResp.json();
            const qData = await qualityResp.json();

            data.recognized.forEach(student => {
                if (!recognizedIds.has(student.id)) {
                    recognizedIds.add(student.id);
                    addRecognizedItem(student);
                    recognizedCount++;
                    if (liveCounterNum) liveCounterNum.textContent = recognizedCount;
                }
            });

            if (qualityText) qualityText.textContent = qData.message || '';
        } catch {}
    }

    function addRecognizedItem(student) {
        if (recognizedList.querySelector('.empty-state')) recognizedList.innerHTML = '';
        const now  = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const item = document.createElement('div');
        item.className = 'recog-item';
        item.innerHTML = `
            <div class="recog-avatar">
                <img src="https://api.dicebear.com/7.x/shapes/svg?seed=${encodeURIComponent(student.name)}&backgroundColor=0a0b14" alt="${student.name}">
            </div>
            <div style="flex:1;min-width:0">
                <div class="recog-name">${student.name}</div>
                <div class="recog-roll">Roll: ${student.roll_no} &nbsp;·&nbsp; ${now}</div>
            </div>
            <div class="recog-check"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></div>
        `;
        recognizedList.prepend(item);
        showToast(`${student.name} marked Present ✓`, 'success');
    }
}

// ─── Reports Chart ────────────────────────────────────────────────────────────
function initReportsPage() {
    let chart = null;

    window._renderReportsChart = function(summary) {
        const ctx = document.getElementById('attendanceChart');
        if (!ctx) return;
        if (chart) chart.destroy();
        const labels = summary.map(s => s.name);
        const values = summary.map(s => s.percentage);
        const colors = values.map(v => v >= 75 ? 'rgba(16,185,129,0.75)' : v >= 50 ? 'rgba(245,158,11,0.75)' : 'rgba(239,68,68,0.75)');
        const borders = values.map(v => v >= 75 ? '#10b981' : v >= 50 ? '#f59e0b' : '#ef4444');

        chart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Attendance %',
                    data: values,
                    backgroundColor: colors,
                    borderColor: borders,
                    borderWidth: 1.5,
                    borderRadius: 7,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(14,16,36,0.95)',
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1,
                        titleColor: '#f1f5f9',
                        bodyColor: '#94a3b8',
                        padding: 12,
                        callbacks: { label: c => `Attendance: ${c.parsed.y}%` }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true, max: 100,
                        ticks: { color: '#475569', callback: v => v + '%', font: { size: 11 } },
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    },
                    x: {
                        ticks: { color: '#475569', font: { size: 11 } },
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    }
                }
            }
        });
    };
}

// ─── Dashboard Chart ──────────────────────────────────────────────────────────
function initDashboard() {
    const ctx = document.getElementById('trendChart');
    if (!ctx) return;
    const labels = JSON.parse(ctx.dataset.labels || '[]');
    const counts  = JSON.parse(ctx.dataset.counts  || '[]');

    const c2d      = ctx.getContext('2d');
    const gradient = c2d.createLinearGradient(0, 0, 0, 280);
    gradient.addColorStop(0, 'rgba(0,245,255,0.22)');
    gradient.addColorStop(1, 'rgba(0,245,255,0.00)');

    window.dashboardChart = new Chart(c2d, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Students Present',
                data: counts,
                borderColor: '#00f5ff',
                backgroundColor: gradient,
                borderWidth: 2.5,
                pointBackgroundColor: '#00f5ff',
                pointBorderColor: 'rgba(0,245,255,0.4)',
                pointBorderWidth: 3,
                pointRadius: 5,
                pointHoverRadius: 8,
                tension: 0.45,
                fill: true,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(6,6,16,0.96)',
                    borderColor: 'rgba(0,245,255,0.3)',
                    borderWidth: 1,
                    titleColor: '#e8eaf6',
                    bodyColor: '#8a9bbf',
                    padding: 12, cornerRadius: 8,
                    callbacks: { label: c => ` Present: ${c.parsed.y}` }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#4a5578', stepSize: 1, font: { size: 11 } },
                    grid: { color: 'rgba(255,255,255,0.04)' }
                },
                x: {
                    ticks: { color: '#4a5578', font: { size: 11 } },
                    grid: { color: 'rgba(255,255,255,0.04)' }
                }
            }
        }
    });
}

// ─── Live Dashboard (SSE) ─────────────────────────────────────────────────────
function initLiveDashboard() {
    const tableBody = document.getElementById('attendanceTableBody');
    if (!tableBody) return; // Only execute on the dashboard page

    const evtSource = new EventSource('/api/stream');
    evtSource.onmessage = function(event) {
        if (event.data === 'ping') return;
        try {
            const data = JSON.parse(event.data);
            const stats = data.stats;
            const records = data.records;

            // Helper to update counter without jarring jump, allowing CSS pop
            const updateCounter = (id, val) => {
                const el = document.getElementById(id);
                if (el && el.innerText != val) {
                    el.innerText = val;
                    el.setAttribute('data-target', val);
                    el.style.transform = 'scale(1.1)';
                    el.style.color = 'var(--accent-green)';
                    setTimeout(() => {
                        el.style.transform = 'scale(1)';
                        el.style.color = '';
                    }, 300);
                }
            };

            updateCounter('statTotalStudents', stats.total_students);
            updateCounter('statPresentToday', stats.present_today);
            updateCounter('statAbsentToday', stats.absent_today);
            
            const rate = stats.total_students > 0 ? Math.round((stats.present_today / stats.total_students) * 100) : 0;
            updateCounter('statAttendanceRate', rate);

            // Update table
            if (records && records.length > 0) {
                // If the table was empty, we need to show it instead of the empty state
                const empty = document.querySelector('.card .empty-state');
                const tableWrap = document.querySelector('.card .table-wrap');
                if (empty) empty.style.display = 'none';
                if (tableWrap) tableWrap.style.display = 'block';
                else if (empty && !tableWrap) {
                    // Force refresh if the table container didn't exist at all
                    window.location.reload(); 
                    return;
                }
                
                tableBody.innerHTML = records.map(r => `
                    <tr>
                        <td>
                            <div class="table-name-cell">
                                <img src="https://api.dicebear.com/7.x/shapes/svg?seed=${encodeURIComponent(r.name)}&backgroundColor=0a0b14,020205" alt="${r.name} avatar" class="table-avatar" />
                                ${r.name}
                            </div>
                        </td>
                        <td>${r.roll_no}</td>
                        <td>${r.time}</td>
                        <td><span class="badge badge-green">${r.status}</span></td>
                    </tr>
                `).join('');
            }
            
            // Update the trend chart (last point is today)
            if (window.dashboardChart) {
                const ds = window.dashboardChart.data.datasets[0];
                const lastIdx = ds.data.length - 1;
                if (lastIdx >= 0 && ds.data[lastIdx] !== stats.present_today) {
                    ds.data[lastIdx] = stats.present_today;
                    window.dashboardChart.update();
                }
            }

        } catch (e) {
            console.error('Error parsing SSE:', e);
        }
    };
    
    evtSource.onerror = function() {
        console.warn("SSE stream disconnected. Reconnecting automatically...");
    };
}

// ─── Page‑load card animations ────────────────────────────────────────────────
function initPageAnimations() {
    const cards = document.querySelectorAll('.card, .stat-card, .feature-card');
    if (!('IntersectionObserver' in window)) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, i) => {
            if (entry.isIntersecting) {
                entry.target.style.animationDelay = (i * 0.06) + 's';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    cards.forEach(card => observer.observe(card));
}

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initMobileSidebar();
    initNotifications();
    initGreeting();
    initCounters();
    initPageAnimations();
    initRegisterPage();
    initAttendancePage();
    initReportsPage();
    initDashboard();
    initLiveDashboard();
});
