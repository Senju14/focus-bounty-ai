/**
 * FocusBounty - Discipline AI Frontend
 * Face & Eye tracking with voice selection
 */

let ws = null;
let sessionId = null;
let sessionStartTime = null;
let mediaStream = null;
let frameInterval = null;
let timerInterval = null;
let interventionCount = 0;
let totalDecisions = 0;
let isCameraOff = false;
let ttsEnabled = true;
let focusStreak = 0;
let selectedVoice = 'female';

const dashboardView = document.getElementById('dashboard-view');
const roomView = document.getElementById('room-view');
const goalInput = document.getElementById('goal-input');
const strictnessSlider = document.getElementById('strictness');
const strictnessValue = document.getElementById('strictness-value');
const voiceSelect = document.getElementById('voice-select');
const webcamFeed = document.getElementById('webcam-feed');
const videoStage = document.getElementById('video-stage');
const sessionTimer = document.getElementById('session-timer');
const currentGoalDisplay = document.getElementById('current-goal-display');
const aiStatusText = document.getElementById('ai-status-text');
const statusIconContainer = document.getElementById('status-icon-container');
const chatFeed = document.getElementById('chat-feed');
const attentionScore = document.getElementById('attention-score');
const engagementStats = document.getElementById('engagement-stats');
const focusPercentage = document.getElementById('focus-percentage');
const streakStats = document.getElementById('streak-stats');
const statusBadge = document.getElementById('status-badge');
const clockDisplay = document.getElementById('clock-display');
const notifications = document.getElementById('notifications');
const decisionsCount = document.getElementById('decisions-count');
const interventionCountEl = document.getElementById('intervention-count');

// Voice configurations
const VOICE_CONFIGS = {
    female: { pitch: 1.1, rate: 1.0, voiceMatch: ['Female', 'Zira', 'Samantha', 'Google UK English Female'] },
    male: { pitch: 0.9, rate: 0.95, voiceMatch: ['Male', 'David', 'Daniel', 'Google UK English Male'] }
};

document.addEventListener('DOMContentLoaded', () => {
    strictnessSlider?.addEventListener('input', () => {
        strictnessValue.textContent = strictnessSlider.value;
    });

    voiceSelect?.addEventListener('change', (e) => {
        selectedVoice = e.target.value;
        localStorage.setItem('voice-type', selectedVoice);
        testVoice();
    });

    // Load saved voice
    const savedVoice = localStorage.getItem('voice-type');
    if (savedVoice && voiceSelect) {
        voiceSelect.value = savedVoice;
        selectedVoice = savedVoice;
    }

    updateClock();
    setInterval(updateClock, 1000);

    showStatus('Connecting...', 'loading');
    connectWebSocket();

    // Preload voices
    speechSynthesis.getVoices();
    speechSynthesis.onvoiceschanged = () => speechSynthesis.getVoices();
});

function testVoice() {
    speak("Voice activated. I'm watching you.", false);
}

function updateClock() {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const hour12 = hours % 12 || 12;
    if (clockDisplay) clockDisplay.textContent = `${hour12}:${minutes} ${ampm}`;
}

function showStatus(message, type = 'info') {
    const statusEl = document.getElementById('connection-status');
    if (statusEl) {
        statusEl.textContent = message;
        statusEl.className = `connection-status ${type}`;
    }
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname || 'localhost';
    const port = window.location.port || 8000;
    const wsUrl = `${protocol}//${host}:${port}/ws/focus`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        showStatus('Connected', 'success');
        addChatMessage('System', '🟢 Connected to Discipline AI', 'system');
    };

    ws.onclose = () => {
        showStatus('Reconnecting...', 'warning');
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = () => showStatus('Connection error', 'error');

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
}

function handleMessage(data) {
    switch (data.type) {
        case 'session_started':
            sessionId = data.session_id;
            sessionStartTime = Date.now();
            startFrameCapture();
            addChatMessage('System', '👁️ Discipline session started. I see everything.', 'success');
            showStatus('Monitoring', 'success');
            break;

        case 'session_stopped':
            stopFrameCapture();
            showSessionSummary(data.stats);
            break;

        case 'update':
            handleUpdate(data);
            break;
    }
}

async function joinRoom() {
    const goal = goalInput?.value.trim() || 'Stay disciplined';

    dashboardView.classList.add('hidden');
    roomView.classList.remove('hidden');

    if (currentGoalDisplay) currentGoalDisplay.textContent = goal;
    interventionCount = 0;
    totalDecisions = 0;
    focusStreak = 0;
    updateCounters();

    showStatus('Starting camera...', 'loading');

    try {
        mediaStream = await navigator.mediaDevices.getUserMedia({
            video: { width: 1280, height: 720, facingMode: 'user' },
            audio: false
        });
        webcamFeed.srcObject = mediaStream;

        addChatMessage('System', '📷 Camera active. Face & eye tracking enabled.', 'success');
        lucide.createIcons();

        if (ws?.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'start',
                strictness: parseInt(strictnessSlider?.value || 7),
                goal: goal
            }));
        }

        // Initial voice
        if (ttsEnabled) {
            setTimeout(() => speak("Discipline session started. I'm watching you."), 1000);
        }

    } catch (err) {
        console.error('Camera error:', err);
        showNotification('Camera access denied', 'danger');
        roomView.classList.add('hidden');
        dashboardView.classList.remove('hidden');
    }
}

function stopSession() {
    ws?.readyState === WebSocket.OPEN && ws.send(JSON.stringify({ type: 'stop' }));

    mediaStream?.getTracks().forEach(track => track.stop());
    mediaStream = null;

    stopFrameCapture();

    roomView.classList.add('hidden');
    dashboardView.classList.remove('hidden');

    sessionId = null;
    sessionStartTime = null;
    showStatus('Ended', 'info');
}

function toggleCamera() {
    isCameraOff = !isCameraOff;
    const camBtn = document.getElementById('cam-btn');
    const camIcon = camBtn?.querySelector('i');

    if (isCameraOff) {
        camBtn?.classList.add('muted');
        camIcon?.setAttribute('data-lucide', 'video-off');
        webcamFeed.style.opacity = '0.3';
    } else {
        camBtn?.classList.remove('muted');
        camIcon?.setAttribute('data-lucide', 'video');
        webcamFeed.style.opacity = '1';
    }
    lucide.createIcons();
}

function toggleTTS() {
    ttsEnabled = !ttsEnabled;
    const ttsBtn = document.getElementById('tts-btn');

    if (ttsEnabled) {
        ttsBtn?.classList.remove('muted');
        addChatMessage('System', '🔊 Voice enabled', 'system');
    } else {
        ttsBtn?.classList.add('muted');
        addChatMessage('System', '🔇 Voice disabled', 'system');
    }
}

function startFrameCapture() {
    frameInterval = setInterval(captureAndSendFrame, 1000);
    timerInterval = setInterval(updateSessionTimer, 1000);
    updateSessionTimer();
}

function stopFrameCapture() {
    clearInterval(frameInterval);
    clearInterval(timerInterval);
    frameInterval = null;
    timerInterval = null;
}

function captureAndSendFrame() {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    if (!webcamFeed || webcamFeed.readyState < 2) return;
    if (isCameraOff) return;

    const canvas = document.createElement('canvas');
    canvas.width = 640;
    canvas.height = 480;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(webcamFeed, 0, 0, canvas.width, canvas.height);

    ws.send(JSON.stringify({
        type: 'frame',
        image: canvas.toDataURL('image/jpeg', 0.7)
    }));
}

function updateSessionTimer() {
    if (!sessionStartTime) return;
    const elapsed = Math.floor((Date.now() - sessionStartTime) / 1000);
    const mins = Math.floor(elapsed / 60).toString().padStart(2, '0');
    const secs = (elapsed % 60).toString().padStart(2, '0');
    if (sessionTimer) sessionTimer.textContent = `${mins}:${secs}`;
}

function handleUpdate(data) {
    const perception = data.perception || {};
    const decision = data.decision || {};

    totalDecisions++;
    focusStreak = decision.focus_streak || 0;

    const attention = Math.round((perception.attention_score || 1) * 100);
    const status = perception.discipline_status || 'focused';

    if (attentionScore) attentionScore.textContent = `${attention}%`;
    if (engagementStats) engagementStats.textContent = `${attention}%`;
    if (streakStats) streakStats.textContent = focusStreak.toString();

    updateCounters();
    updateDisciplineStatus(status, perception);
    drawDetections(perception.boxes || []);

    if (decision.should_intervene) {
        interventionCount++;
        updateCounters();
        handleIntervention(decision);
    }
}

function updateCounters() {
    if (decisionsCount) decisionsCount.textContent = totalDecisions.toString();
    if (interventionCountEl) interventionCountEl.textContent = interventionCount.toString();
}

function updateDisciplineStatus(status, perception) {
    videoStage?.classList.remove('status-focused', 'status-warning', 'status-distracted', 'status-away');

    const statusConfig = {
        focused: { class: 'status-focused', text: '👁️ FOCUSED', dot: 'status-dot-green', badge: 'FOCUSED' },
        distracted: { class: 'status-warning', text: '⚠️ DISTRACTED', dot: 'status-dot-yellow', badge: 'DISTRACTED' },
        unfocused: { class: 'status-warning', text: '😐 UNFOCUSED', dot: 'status-dot-yellow', badge: 'UNFOCUSED' },
        drowsy: { class: 'status-distracted', text: '😴 DROWSY', dot: 'status-dot-red', badge: 'DROWSY' },
        away: { class: 'status-away', text: '👻 AWAY', dot: 'status-dot-red', badge: 'AWAY' },
        absent: { class: 'status-distracted', text: '🚨 ABSENT', dot: 'status-dot-red', badge: 'ABSENT' }
    };

    const config = statusConfig[status] || statusConfig.focused;

    videoStage?.classList.add(config.class);
    if (aiStatusText) aiStatusText.textContent = config.text;
    if (statusIconContainer) statusIconContainer.className = `status-dot ${config.dot}`;
    if (statusBadge) {
        statusBadge.innerHTML = `<span class="status-text ${status}">${config.badge}</span>`;
    }
}

function drawDetections(boxes) {
    const overlay = document.getElementById('detection-overlay');
    if (overlay) overlay.innerHTML = '';
    if (!boxes?.length) return;

    boxes.forEach(box => {
        const div = document.createElement('div');
        div.className = `detection-box ${box.label}`;

        div.style.left = `${(1 - box.x - box.w) * 100}%`;
        div.style.top = `${box.y * 100}%`;
        div.style.width = `${box.w * 100}%`;
        div.style.height = `${box.h * 100}%`;

        const label = document.createElement('span');
        label.className = 'detection-label';
        label.textContent = box.label === 'face' ? '👤 FACE' : box.label === 'eye' ? '👁️ EYE' : '🧍 PERSON';
        div.appendChild(label);

        overlay?.appendChild(div);
    });
}

function handleIntervention(decision) {
    const message = decision.message || 'Focus!';
    const severity = decision.severity || 'low';
    const status = decision.discipline_status || 'distracted';

    const severityEmoji = {
        positive: '🌟',
        low: '⚠️',
        medium: '😤',
        high: '🔥',
        critical: '🚨'
    }[severity] || '⚡';

    const chatType = severity === 'positive' ? 'success' :
        severity === 'critical' ? 'intervention' : 'warning';

    addChatMessage(`Discipline ${severityEmoji}`, message, chatType);
    showNotification(message, chatType === 'success' ? 'success' : 'warning');

    if (decision.tts_enabled && ttsEnabled) speak(message);
}

function speak(text, cancelPrevious = true) {
    if (cancelPrevious) speechSynthesis.cancel();

    const cleanText = text.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '');

    const utterance = new SpeechSynthesisUtterance(cleanText);
    const config = VOICE_CONFIGS[selectedVoice] || VOICE_CONFIGS.female;

    utterance.pitch = config.pitch;
    utterance.rate = config.rate;
    utterance.volume = 0.9;

    const voices = speechSynthesis.getVoices();
    const matchingVoice = voices.find(v =>
        config.voiceMatch.some(match => v.name.includes(match))
    );
    if (matchingVoice) utterance.voice = matchingVoice;

    speechSynthesis.speak(utterance);
}

function addChatMessage(sender, message, type = 'default') {
    const div = document.createElement('div');
    div.className = `chat-msg ${type}`;
    div.innerHTML = `<span class="chat-msg-time">${sender}</span>${message}`;
    chatFeed?.appendChild(div);
    if (chatFeed) chatFeed.scrollTop = chatFeed.scrollHeight;

    while (chatFeed?.children.length > 50) chatFeed.removeChild(chatFeed.firstChild);
}

function showNotification(message, type = 'warning') {
    const div = document.createElement('div');
    div.className = `notification-toast ${type}`;

    const icon = type === 'danger' ? 'alert-octagon' : type === 'success' ? 'check-circle' : 'alert-triangle';
    div.innerHTML = `<i data-lucide="${icon}" class="w-5 h-5"></i><span class="font-medium">${message}</span>`;

    notifications?.appendChild(div);
    lucide.createIcons();

    setTimeout(() => {
        div.style.opacity = '0';
        div.style.transform = 'translateY(-20px)';
        setTimeout(() => div.remove(), 300);
    }, 4000);
}

function showSessionSummary(stats) {
    if (!stats) return;

    const duration = stats.session_duration_minutes?.toFixed(1) || '0';
    const focusPct = stats.focus_percentage?.toFixed(0) || '100';
    const message = `📊 Session: ${duration}min | Focus: ${focusPct}% | Alerts: ${stats.total_interventions || 0}`;

    addChatMessage('Summary', message, 'success');
    showNotification('Session complete!', 'success');

    if (ttsEnabled) speak(`Session complete. Your focus was ${focusPct} percent.`);
}
