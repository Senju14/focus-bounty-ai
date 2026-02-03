const videoElement = document.getElementById('input_video');
const canvasElement = document.getElementById('output_canvas');
const canvasCtx = canvasElement.getContext('2d');
const logPanel = document.getElementById('logPanel');

// HUD Elements
const hudFace = document.getElementById('hudFace');
const hudEAR = document.getElementById('hudEAR');
const hudIris = document.getElementById('hudIris');
const hudYaw = document.getElementById('hudYaw');
const monitorStatus = document.getElementById('monitorStatus');

// Stats Elements
const focusTimerEl = document.getElementById('focusTimer');
const streakCounterEl = document.getElementById('streakCounter');
const roastCounterEl = document.getElementById('roastCounter');
const recoveryRateEl = document.getElementById('recoveryRate');
const roastModal = document.getElementById('roastModal');
const roastTextEl = document.getElementById('roastText');
const memeOverlay = document.getElementById('memeOverlay');
const memeImage = document.getElementById('memeImage');

let ws = null;
let lastTriggerTime = 0;
let sessionStartTime = 0;
let timerInterval = null;
let roasts = 0;
let recoveryTimes = [];
let lastRoastTime = 0;
let isMonitoring = false;
let distractionStartTime = 0;
let streakSeconds = 0;

// Configuration
const TRIGGER_COOLDOWN = 12000;
const WS_URL = `ws://${window.location.host}/ws/focus`;

// --- VOICE SETUP ---
let voices = [];
let currentVoiceMode = 'auto'; // auto, male, female

function loadVoices() {
    voices = window.speechSynthesis.getVoices();
}
// Initialize voices
window.speechSynthesis.onvoiceschanged = loadVoices;
if (window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = loadVoices;
}

// Listen for Voice Change UI Events
window.addEventListener('voice-change', (e) => {
    currentVoiceMode = e.detail.mode;
    log(`Voice mode set to: ${currentVoiceMode}`);
});

// --- PRAISE & MEME LOGIC ---
const PRAISE_MEMES = [
    '/static/assets/memes/positive/good_job_1.png',
    '/static/assets/memes/positive/good_job_2.png',
    '/static/assets/memes/positive/good_job_3.png'
];

function triggerPraise() {
    const randomMeme = PRAISE_MEMES[Math.floor(Math.random() * PRAISE_MEMES.length)];
    memeImage.src = randomMeme;
    memeOverlay.classList.add('active');

    // Praise Speech
    const praises = ["Incredible focus.", "You are a machine.", "Zone locked in.", "Unstoppable."];
    const praiseText = praises[Math.floor(Math.random() * praises.length)];
    speak(praiseText);

    // Hide after 4s
    setTimeout(() => {
        memeOverlay.classList.remove('active');
    }, 4000);
}

function playSiren() {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.value = 440;
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();

    // Siren effect
    let time = ctx.currentTime;
    for (let i = 0; i < 10; i++) {
        osc.frequency.linearRampToValueAtTime(880, time + 0.5);
        osc.frequency.linearRampToValueAtTime(440, time + 1.0);
        time += 1.0;
    }
    osc.stop(time);

    // Flash Screen
    const flash = document.createElement('div');
    flash.style.position = 'fixed';
    flash.style.top = '0'; flash.style.left = '0'; flash.style.width = '100vw'; flash.style.height = '100vh';
    flash.style.background = 'red'; flash.style.opacity = '0.5'; flash.style.zIndex = '9999';
    flash.style.pointerEvents = 'none';
    flash.style.animation = 'blink 0.2s infinite';
    document.body.appendChild(flash);
    setTimeout(() => flash.remove(), 2000);

    const style = document.createElement('style');
    style.innerHTML = `@keyframes blink { 0% { opacity: 0.5; } 50% { opacity: 0; } 100% { opacity: 0.5; } }`;
    document.head.appendChild(style);
}

function log(msg) {
    const time = new Date().toLocaleTimeString();
    const div = document.createElement('div');
    div.innerHTML = `<span style="color: var(--accent-blue)">[${time}]</span> ${msg}`;
    logPanel.prepend(div);
}

function speak(text) {
    if (voices.length === 0) loadVoices();
    const utterance = new SpeechSynthesisUtterance(text);

    // Voice Selection Logic
    let chosenVoice = null;

    if (currentVoiceMode === 'female') {
        chosenVoice = voices.find(v => v.name.includes('Female') || v.name.includes('Zira') || v.name.includes('Google US English'));
    } else if (currentVoiceMode === 'male') {
        chosenVoice = voices.find(v => v.name.includes('Male') || v.name.includes('David') || v.name.includes('Mark'));
    }

    if (!chosenVoice) {
        // Random Fallback
        const langVoices = voices.filter(v => v.lang.startsWith('en'));
        chosenVoice = langVoices.length > 0 ? langVoices[Math.floor(Math.random() * langVoices.length)] : voices[0];
    }

    utterance.voice = chosenVoice;
    utterance.pitch = 0.8 + Math.random() * 0.4;
    utterance.rate = 1.1;
    window.speechSynthesis.speak(utterance);
}

function triggerRoast(text) {
    lastRoastTime = Date.now();
    roasts++;
    roastCounterEl.textContent = roasts;
    streakSeconds = 0; // Reset streak on roast
    streakCounterEl.textContent = '0m';

    roastTextEl.textContent = `"${text}"`;
    roastModal.classList.add('active');
    speak(text);
    setTimeout(() => { roastModal.classList.remove('active'); }, 6000);
}

function updateRecovery() {
    // Only update stats if we have been distracted previously
    if (lastRoastTime > 0) {
        const diff = (Date.now() - lastRoastTime) / 1000;
        recoveryTimes.push(diff);
        const avg = recoveryTimes.reduce((a, b) => a + b, 0) / recoveryTimes.length;
        if (recoveryRateEl) recoveryRateEl.textContent = avg.toFixed(1);
        lastRoastTime = 0;
    }
}

// MediaPipe Logic - IRIS TRACKING
async function onResults(results) {
    if (!isMonitoring) return;

    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    canvasCtx.globalCompositeOperation = 'source-over';

    if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
        const landmarks = results.multiFaceLandmarks[0];

        // Mesh Toggle
        const showMesh = document.getElementById('meshToggle') ? document.getElementById('meshToggle').checked : true;
        if (showMesh) {
            drawConnectors(canvasCtx, landmarks, FACEMESH_TESSELATION, { color: '#C0C0C070', lineWidth: 1 });
        }

        // Eye Aspect Ratio (EAR)
        const leftEyeTop = landmarks[159].y;
        const leftEyeBot = landmarks[145].y;
        const ear = Math.abs(leftEyeTop - leftEyeBot);
        hudEAR.textContent = ear.toFixed(3);

        // Head Pose
        const nose = landmarks[1].x;
        const leftCheek = landmarks[234].x;
        const rightCheek = landmarks[454].x;
        const yaw = (nose - leftCheek) / (rightCheek - leftCheek);
        hudYaw.textContent = yaw.toFixed(2);

        // Iris Tracking
        let irisScore = 0.5;
        let hasIris = landmarks.length > 468;

        if (hasIris) {
            function getIrisRatio(innerIdx, outerIdx, irisIdx) {
                const inner = landmarks[innerIdx];
                const outer = landmarks[outerIdx];
                const iris = landmarks[irisIdx];
                const totalDist = Math.abs(outer.x - inner.x);
                const irisDist = Math.abs(iris.x - inner.x);
                return irisDist / totalDist;
            }
            const leftRatio = getIrisRatio(33, 133, 468);
            const rightRatio = getIrisRatio(362, 263, 473);
            irisScore = (leftRatio + rightRatio) / 2;

            if (showMesh) {
                const irisL = landmarks[468];
                const irisR = landmarks[473];
                canvasCtx.fillStyle = '#00FFFF';
                canvasCtx.beginPath(); canvasCtx.arc(irisL.x * canvasElement.width, irisL.y * canvasElement.height, 3, 0, 2 * Math.PI); canvasCtx.fill();
                canvasCtx.beginPath(); canvasCtx.arc(irisR.x * canvasElement.width, irisR.y * canvasElement.height, 3, 0, 2 * Math.PI); canvasCtx.fill();
            }
        }
        hudIris.textContent = hasIris ? irisScore.toFixed(2) : "N/A";

        // Logic
        let status = "FOCUSED";
        let reason = "";

        if (ear < 0.012) {
            status = "SLEEPING";
            reason = "User is sleeping / Eyes closed";
        }
        else if (yaw < 0.25 || yaw > 0.75) {
            status = "AWAY";
            reason = "User looking away (Head)";
        }
        else if (hasIris && (irisScore < 0.22 || irisScore > 0.78)) {
            status = "SIDE_EYE";
            reason = "User side-eyeing distractions";
        }

        if (status !== "FOCUSED") {
            monitorStatus.innerHTML = `<span style="color:var(--accent-red)">Warning: ${status}</span>`;
            sendDistraction(reason);
            // Reset Streak
            streakSeconds = 0;
            streakCounterEl.textContent = '0m';
        } else {
            monitorStatus.innerHTML = `<span style="color:var(--accent-green)">Focused</span>`;
            updateRecovery();
        }

        hudFace.textContent = "LOCKED";
        hudFace.style.color = "#00FF00";

    } else {
        hudFace.textContent = "LOST";
        hudFace.style.color = "#FF0000";
        sendDistraction("User left the desk");
        streakSeconds = 0; // Reset streak
    }
    canvasCtx.restore();
}

// MediaPipe Init
const faceMesh = new FaceMesh({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`
});
faceMesh.setOptions({
    maxNumFaces: 1,
    refineLandmarks: true,
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5
});
faceMesh.onResults(onResults);

const camera = new Camera(videoElement, {
    onFrame: async () => {
        await faceMesh.send({ image: videoElement });
    },
    width: 640,
    height: 480
});

// Helper for sending frames
function sendDistraction(reason) {
    const now = Date.now();
    if (now - lastTriggerTime < TRIGGER_COOLDOWN) return;

    if (ws && ws.readyState === WebSocket.OPEN) {
        lastTriggerTime = now;
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = videoElement.videoWidth;
        tempCanvas.height = videoElement.videoHeight;
        tempCanvas.getContext('2d').drawImage(videoElement, 0, 0);
        const imageData = tempCanvas.toDataURL('image/jpeg', 0.7);

        ws.send(JSON.stringify({ image: imageData, reason: reason }));
        monitorStatus.innerHTML = `<span style="color:var(--accent-red)">Detecting Distraction...</span>`;
        log(`Trigger: ${reason}`);
    }
}

// Event Listeners
document.getElementById('startBtn').onclick = () => {
    isMonitoring = true;
    camera.start();
    sessionStartTime = Date.now();

    ws = new WebSocket(WS_URL);
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.tease) {
            triggerRoast(data.tease);
            log(`Roast: ${data.tease}`);

            if (document.hidden) {
                new Notification("FocusGuard Alert", { body: data.tease });
            }
        }
    };

    timerInterval = setInterval(() => {
        const diff = Math.floor((Date.now() - sessionStartTime) / 1000);
        const m = Math.floor(diff / 60).toString().padStart(2, '0');
        const s = (diff % 60).toString().padStart(2, '0');
        focusTimerEl.textContent = `${m}:${s}`;

        // Update Streak Timer
        if (monitorStatus.innerText.includes("Focused")) {
            streakSeconds++;
            // Format streak
            const sm = Math.floor(streakSeconds / 60);
            const ss = streakSeconds % 60;
            streakCounterEl.textContent = `${sm}m ${ss}s`;

            // Trigger Praise every 20s (Demo) or 5 mins (Real)
            // Using 20s for demo purposes as implied by "lâu lâu" (occasionally)
            if (streakSeconds > 0 && streakSeconds % 30 === 0) {
                triggerPraise();
                log("God Mode Streak! +100 Aura");
            }
        }

    }, 1000);

    // Tab Visibility
    document.addEventListener("visibilitychange", () => {
        if (document.hidden && isMonitoring) {
            const reason = "User switched tabs/windows";
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ reason: reason }));
                new Notification("FocusGuard Alert", {
                    body: "GET BACK TO WORK! The Toxic Coach is watching."
                });
                playSiren();
            }
        }
    });

    log("System Armed. Monitoring active.");
};

document.getElementById('stopBtn').onclick = () => {
    isMonitoring = false;
    camera.stop();
    if (ws) ws.close();
    clearInterval(timerInterval);
    log("Session ended.");
    monitorStatus.innerHTML = "Session Paused";

    document.getElementById('reportCardStyle').style.display = 'block';
    document.getElementById('rcDuration').textContent = focusTimerEl.textContent;
    document.getElementById('rcRoasts').textContent = roasts;
    if (recoveryRateEl) document.getElementById('rcRecovery').textContent = recoveryRateEl.textContent;

    const grades = ["F", "D-", "C", "B", "A+"];
    const score = Math.max(0, 4 - Math.floor(roasts / 2));
    const grade = grades[score] || "F";
    const comments = ["Disgraceful.", "Barely conscious.", "Mediocre.", "Not bad.", "Absolute machine."];

    document.getElementById('rcVerdict').textContent = `Grade: ${grade}. ${comments[score]}`;
};
