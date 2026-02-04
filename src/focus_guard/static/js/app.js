/**
 * FocusGuard AI - Main Application
 * Browser-based focus monitoring with AI feedback
 */

// =============================================================================
// DOM Elements
// =============================================================================

var videoElement = document.getElementById("input_video");
var canvasElement = document.getElementById("output_canvas");
var canvasCtx = canvasElement.getContext("2d");
var logPanel = document.getElementById("logPanel");
var hudFace = document.getElementById("hudFace");
var hudEAR = document.getElementById("hudEAR");
var hudIris = document.getElementById("hudIris");
var hudYaw = document.getElementById("hudYaw");
var monitorStatus = document.getElementById("monitorStatus");
var focusTimerEl = document.getElementById("focusTimer");
var streakCounterEl = document.getElementById("streakCounter");
var roastCounterEl = document.getElementById("roastCounter");
var recoveryRateEl = document.getElementById("recoveryRate");
var roastModal = document.getElementById("roastModal");
var roastTextEl = document.getElementById("roastText");
var memeOverlay = document.getElementById("memeOverlay");
var memeImage = document.getElementById("memeImage");

// =============================================================================
// State Variables
// =============================================================================

var ws = null;
var lastTriggerTime = 0;
var sessionStartTime = 0;
var timerInterval = null;
var roasts = 0;
var recoveryTimes = [];
var lastRoastTime = 0;
var isMonitoring = false;
var distractionStartTime = 0;
var streakSeconds = 0;
var voices = [];
var currentVoiceMode = "auto";
var isDistracted = false; // Track current distraction state
var warningVisible = false; // Track if warning popup is visible
var floatingCamVisible = false; // Track floating cam state
var focusHistory = []; // Buffer for focus smoothing
var FOCUS_BUFFER_SIZE = 8; // Number of frames to average (prevents flickering)

// =============================================================================
// Configuration
// =============================================================================

var SETTINGS_KEY = "focusguard_settings";
var WS_URL = "ws://" + window.location.host + "/ws/focus";

// Local asset paths
var PRAISE_MEMES = [
    "/static/assets/memes/positive_1.jpg",
    "/static/assets/memes/positive_2.jpg"
];

var ROAST_MEMES = [
    "/static/assets/memes/negative_1.jpg",
    "/static/assets/memes/negative_2.jpg"
];

// Meme Voice Presets (pitch, rate combos)
var MEME_VOICES = {
    "paimon": { pitch: 1.8, rate: 1.3, name: "Paimon" },
    "mickey": { pitch: 1.6, rate: 1.1, name: "Mickey Mouse" },
    "morgan": { pitch: 0.4, rate: 0.85, name: "Morgan Freeman" },
    "chipmunk": { pitch: 2.0, rate: 1.5, name: "Chipmunk" },
    "vader": { pitch: 0.3, rate: 0.7, name: "Darth Vader" },
    "anime": { pitch: 1.5, rate: 1.2, name: "Anime Girl" },
    "robot": { pitch: 0.5, rate: 0.9, name: "Robot" },
    "ghost": { pitch: 0.6, rate: 0.6, name: "Ghostface" }
};

// =============================================================================
// Settings Management
// =============================================================================

function getSettings() {
    var defaults = {
        voiceType: "auto",
        voiceLanguage: "en-US",
        speechRate: 1.1,
        voicePitch: 1.0,
        showMesh: true,
        roastCooldown: 12,
        browserNotifications: true
    };
    var stored = localStorage.getItem(SETTINGS_KEY);
    return stored ? JSON.parse(stored) : defaults;
}

var settings = getSettings();

// =============================================================================
// Voice Setup
// =============================================================================

function loadVoices() {
    voices = window.speechSynthesis.getVoices();
}

window.speechSynthesis.onvoiceschanged = loadVoices;

// Voice & Camera controls
document.addEventListener("DOMContentLoaded", function() {
    // Voice select dropdown
    var voiceSelect = document.getElementById("voiceSelect");
    if (voiceSelect) {
        voiceSelect.addEventListener("change", function() {
            currentVoiceMode = voiceSelect.value;
            var voiceName = voiceSelect.options[voiceSelect.selectedIndex].text;
            log("🎤 Voice: " + voiceName);
            // Test the voice
            speak("Hey! Let's focus!");
        });
    }
    
    // Camera toggle button
    var camToggleBtn = document.getElementById("camToggleBtn");
    if (camToggleBtn) {
        camToggleBtn.addEventListener("click", function() {
            toggleFloatingCam();
        });
    }
    
    settings = getSettings();
    var meshToggle = document.getElementById("meshToggle");
    if (meshToggle) {
        meshToggle.checked = settings.showMesh !== false;
    }
});

// =============================================================================
// Floating Camera Toggle
// =============================================================================

function toggleFloatingCam() {
    var floatingCam = document.getElementById("floatingCam");
    var camToggleBtn = document.getElementById("camToggleBtn");
    var previewVideo = document.getElementById("previewVideo");
    
    if (!floatingCam) return;
    
    floatingCamVisible = !floatingCamVisible;
    
    if (floatingCamVisible) {
        floatingCam.classList.add("active");
        camToggleBtn.classList.add("active");
        // Set video source if monitoring
        if (videoElement.srcObject && previewVideo) {
            previewVideo.srcObject = videoElement.srcObject;
        }
        log("📷 Camera preview ON");
    } else {
        floatingCam.classList.remove("active");
        camToggleBtn.classList.remove("active");
        log("📷 Camera preview OFF");
    }
}

// =============================================================================
// Meme & Feedback Functions
// =============================================================================

function getRandomItem(array) {
    return array[Math.floor(Math.random() * array.length)];
}

function triggerPraise() {
    var randomMeme = getRandomItem(PRAISE_MEMES);
    memeImage.src = randomMeme;
    memeOverlay.classList.add("active");

    var praises = [
        "Incredible focus!",
        "You are a machine!",
        "Zone locked in!",
        "Unstoppable!"
    ];
    speak(getRandomItem(praises));

    setTimeout(function() {
        memeOverlay.classList.remove("active");
    }, 4000);
}

// =============================================================================
// Logging
// =============================================================================

function log(msg) {
    var time = new Date().toLocaleTimeString();
    var div = document.createElement("div");
    div.innerHTML = "<span class='log-time'>[" + time + "]</span> " + msg;
    logPanel.prepend(div);
}

// =============================================================================
// Text-to-Speech
// =============================================================================

function speak(text) {
    if (voices.length === 0) loadVoices();
    settings = getSettings();
    var utterance = new SpeechSynthesisUtterance(text);

    var chosenVoice = null;
    var lang = settings.voiceLanguage || "en-US";
    var voiceType = settings.voiceType || currentVoiceMode;

    // Filter by language first
    var langVoices = voices.filter(function(v) { 
        return v.lang === lang || v.lang.startsWith(lang.split("-")[0]); 
    });
    
    // Check if it's a meme voice
    if (MEME_VOICES[voiceType]) {
        var memeVoice = MEME_VOICES[voiceType];
        utterance.pitch = memeVoice.pitch;
        utterance.rate = memeVoice.rate;
        // Use any available voice
        chosenVoice = langVoices.length > 0 ? langVoices[0] : voices[0];
    } else if (voiceType === "auto" || currentVoiceMode === "auto") {
        // Auto mode: pick random meme voice for fun!
        var memeKeys = Object.keys(MEME_VOICES);
        var randomMeme = memeKeys[Math.floor(Math.random() * memeKeys.length)];
        var autoVoice = MEME_VOICES[randomMeme];
        utterance.pitch = autoVoice.pitch;
        utterance.rate = autoVoice.rate;
        chosenVoice = langVoices.length > 0 ? langVoices[0] : voices[0];
    } else if (voiceType === "female" || currentVoiceMode === "female") {
        chosenVoice = langVoices.find(function(v) {
            var name = v.name.toLowerCase();
            return name.includes("female") || v.name.includes("Zira") || 
                   v.name.includes("Samantha") || name.includes("woman");
        });
        utterance.pitch = 1.2;
        utterance.rate = 1.1;
    } else if (voiceType === "male" || currentVoiceMode === "male") {
        chosenVoice = langVoices.find(function(v) {
            var name = v.name.toLowerCase();
            return name.includes("male") || v.name.includes("David") || 
                   v.name.includes("Mark") || name.includes("man");
        });
        utterance.pitch = 0.9;
        utterance.rate = 1.0;
    }

    if (!chosenVoice) {
        chosenVoice = langVoices.length > 0 ? langVoices[Math.floor(Math.random() * langVoices.length)] : voices[0];
    }

    utterance.voice = chosenVoice;
    window.speechSynthesis.speak(utterance);
}

// =============================================================================
// Roast Functions
// =============================================================================

function triggerRoast(text) {
    lastRoastTime = Date.now();
    roasts++;
    roastCounterEl.textContent = roasts;
    streakSeconds = 0;
    streakCounterEl.textContent = "0m";

    // Show roast meme
    var randomMeme = getRandomItem(ROAST_MEMES);
    var roastMemeEl = document.getElementById("roastMeme");
    if (roastMemeEl) {
        roastMemeEl.src = randomMeme;
        roastMemeEl.classList.remove("roast-meme-hidden");
    }

    roastTextEl.textContent = '"' + text + '"';
    roastModal.classList.add("active");
    speak(text);
    
    setTimeout(function() { 
        roastModal.classList.remove("active");
        if (roastMemeEl) roastMemeEl.classList.add("roast-meme-hidden");
    }, 6000);
}

// =============================================================================
// Focus Smoothing (prevents flickering)
// =============================================================================

function updateFocusBuffer(isFocused) {
    focusHistory.push(isFocused ? 1 : 0);
    if (focusHistory.length > FOCUS_BUFFER_SIZE) {
        focusHistory.shift();
    }
}

function getSmoothedFocus() {
    if (focusHistory.length === 0) return true;
    var sum = focusHistory.reduce(function(a, b) { return a + b; }, 0);
    // Need at least 60% of frames to be "not focused" to trigger distraction
    return sum >= focusHistory.length * 0.4;
}

// =============================================================================
// Recovery Tracking
// =============================================================================

function updateRecovery() {
    if (lastRoastTime > 0) {
        var diff = (Date.now() - lastRoastTime) / 1000;
        recoveryTimes.push(diff);
        var sum = recoveryTimes.reduce(function(a, b) { return a + b; }, 0);
        var avg = sum / recoveryTimes.length;
        if (recoveryRateEl) recoveryRateEl.textContent = avg.toFixed(1);
        lastRoastTime = 0;
    }
}

// =============================================================================
// MediaPipe Face Detection
// =============================================================================
function onResults(results) {
    if (!isMonitoring) return;

    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    canvasCtx.globalCompositeOperation = "source-over";

    if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
        var landmarks = results.multiFaceLandmarks[0];

        // Mesh Toggle
        var showMesh = document.getElementById("meshToggle") ? document.getElementById("meshToggle").checked : true;
        if (showMesh) {
            drawConnectors(canvasCtx, landmarks, FACEMESH_TESSELATION, { color: "#C0C0C070", lineWidth: 1 });
        }

        // Eye Aspect Ratio (EAR)
        var leftEyeTop = landmarks[159].y;
        var leftEyeBot = landmarks[145].y;
        var ear = Math.abs(leftEyeTop - leftEyeBot);
        hudEAR.textContent = ear.toFixed(3);

        // Head Pose
        var nose = landmarks[1].x;
        var leftCheek = landmarks[234].x;
        var rightCheek = landmarks[454].x;
        var yaw = (nose - leftCheek) / (rightCheek - leftCheek);
        hudYaw.textContent = yaw.toFixed(2);

        // Iris Tracking
        var irisScore = 0.5;
        var hasIris = landmarks.length > 468;

        if (hasIris) {
            function getIrisRatio(innerIdx, outerIdx, irisIdx) {
                var inner = landmarks[innerIdx];
                var outer = landmarks[outerIdx];
                var iris = landmarks[irisIdx];
                var totalDist = Math.abs(outer.x - inner.x);
                var irisDist = Math.abs(iris.x - inner.x);
                return irisDist / totalDist;
            }
            var leftRatio = getIrisRatio(33, 133, 468);
            var rightRatio = getIrisRatio(362, 263, 473);
            irisScore = (leftRatio + rightRatio) / 2;

            if (showMesh) {
                var irisL = landmarks[468];
                var irisR = landmarks[473];
                canvasCtx.fillStyle = "#00FFFF";
                canvasCtx.beginPath(); 
                canvasCtx.arc(irisL.x * canvasElement.width, irisL.y * canvasElement.height, 3, 0, 2 * Math.PI); 
                canvasCtx.fill();
                canvasCtx.beginPath(); 
                canvasCtx.arc(irisR.x * canvasElement.width, irisR.y * canvasElement.height, 3, 0, 2 * Math.PI); 
                canvasCtx.fill();
            }
        }
        hudIris.textContent = hasIris ? irisScore.toFixed(2) : "N/A";

        // Determine raw focus status
        var rawFocused = true;
        var reason = "";

        if (ear < 0.010) { // More lenient threshold
            rawFocused = false;
            reason = "User is sleeping / Eyes closed";
        }
        else if (yaw < 0.20 || yaw > 0.80) { // More lenient threshold
            rawFocused = false;
            reason = "User looking away (Head)";
        }

        // Update focus buffer for smoothing
        updateFocusBuffer(rawFocused);
        var smoothedFocus = getSmoothedFocus();

        if (!smoothedFocus) {
            monitorStatus.innerHTML = "<span class='status-warning'>Warning: DISTRACTED</span>";
            if (!isDistracted) {
                isDistracted = true;
                sendDistraction(reason || "User distracted");
            }
            streakSeconds = 0;
            streakCounterEl.textContent = "0m";
        } else {
            monitorStatus.innerHTML = "<span class='status-ok'>Focused</span>";
            if (isDistracted) {
                isDistracted = false;
                updateRecovery();
            }
        }

        hudFace.textContent = "LOCKED";
        hudFace.style.color = "#00FF00";

    } else {
        hudFace.textContent = "LOST";
        hudFace.style.color = "#FF0000";
        updateFocusBuffer(false);
        if (!isDistracted && !getSmoothedFocus()) {
            isDistracted = true;
            sendDistraction("User left the desk");
        }
        streakSeconds = 0;
    }
    canvasCtx.restore();
}

// =============================================================================
// MediaPipe Initialization
// =============================================================================

var faceMesh = new FaceMesh({
    locateFile: function(file) { 
        return "https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/" + file; 
    }
});

faceMesh.setOptions({
    maxNumFaces: 1,
    refineLandmarks: true,
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5
});

faceMesh.onResults(onResults);

var camera = new Camera(videoElement, {
    onFrame: function() {
        return faceMesh.send({ image: videoElement });
    },
    width: 640,
    height: 480
});

// =============================================================================
// WebSocket & Distraction Handling
// =============================================================================
function sendDistraction(reason) {
    var now = Date.now();
    settings = getSettings();
    var cooldown = (settings.roastCooldown || 12) * 1000;
    
    if (now - lastTriggerTime < cooldown) return;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;

    lastTriggerTime = now;
    
    var tempCanvas = document.createElement("canvas");
    tempCanvas.width = videoElement.videoWidth;
    tempCanvas.height = videoElement.videoHeight;
    tempCanvas.getContext("2d").drawImage(videoElement, 0, 0);
    var imageData = tempCanvas.toDataURL("image/jpeg", 0.7);

    ws.send(JSON.stringify({ image: imageData, reason: reason }));
    monitorStatus.innerHTML = "<span class='status-warning'>Detecting Distraction...</span>";
    log("Trigger: " + reason);
    saveActivityLog("[WARNING] " + reason, "warning");
}

// =============================================================================
// Activity Logging
// =============================================================================

function saveActivityLog(message, type) {
    type = type || "info";
    var LOG_KEY = "focusguard_logs";
    var logs = JSON.parse(localStorage.getItem(LOG_KEY) || "[]");
    
    logs.push({
        time: new Date().toLocaleTimeString(),
        message: message,
        type: type
    });
    
    if (logs.length > 500) logs.shift();
    localStorage.setItem(LOG_KEY, JSON.stringify(logs));
}

// =============================================================================
// Session Controls
// =============================================================================
document.getElementById("startBtn").onclick = function() {
    isMonitoring = true;
    isDistracted = false;
    warningVisible = false;
    camera.start();
    sessionStartTime = Date.now();

    // Initialize Face Preview (corner window) after camera starts
    setTimeout(function() {
        var previewVideo = document.getElementById("previewVideo");
        if (previewVideo && videoElement.srcObject) {
            previewVideo.srcObject = videoElement.srcObject;
        }
    }, 500);

    // Initialize WebSocket
    ws = new WebSocket(WS_URL);
    
    ws.onmessage = function(e) {
        var data = JSON.parse(e.data);
        if (!data.tease) return;
        
        // Only show roast if currently distracted
        if (!isDistracted) return;
        
        triggerRoast(data.tease);
        log("Roast: " + data.tease);
        saveActivityLog("[ROAST] " + data.tease, "roast");

        // Browser notification when tab is hidden
        if (document.hidden && settings.browserNotifications) {
            var notification = new Notification("FocusGuard Alert!", { 
                body: data.tease,
                tag: "focusguard-roast",
                requireInteraction: true
            });
            notification.onclick = function() {
                window.focus();
                notification.close();
            };
        }
    };

    // Timer interval
    timerInterval = setInterval(function() {
        var diff = Math.floor((Date.now() - sessionStartTime) / 1000);
        var m = Math.floor(diff / 60).toString().padStart(2, "0");
        var s = (diff % 60).toString().padStart(2, "0");
        focusTimerEl.textContent = m + ":" + s;

        // Update Streak Timer
        if (monitorStatus.innerText.includes("Focused")) {
            streakSeconds++;
            var sm = Math.floor(streakSeconds / 60);
            var ss = streakSeconds % 60;
            streakCounterEl.textContent = sm + "m " + ss + "s";

            // Trigger Praise every 30 seconds
            if (streakSeconds > 0 && streakSeconds % 30 === 0) {
                triggerPraise();
                log("God Mode Streak! +100 Aura");
                saveActivityLog("[PRAISE] God Mode Streak! +100 Aura", "praise");
            }
        }
    }, 1000);

    // Tab Visibility Detection - show message when user switches tab
    document.addEventListener("visibilitychange", handleVisibilityChange);
    log("System Armed. Monitoring active.");
};

function handleVisibilityChange() {
    if (!document.hidden || !isMonitoring) return;
    
    var reason = "User switched tabs/windows";
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ reason: reason }));
        log("⚠️ Tab switched - distraction detected!");
        saveActivityLog("[WARNING] Tab switched - distraction detected!", "warning");
    }
}

document.getElementById("stopBtn").onclick = function() {
    isMonitoring = false;
    isDistracted = false;
    warningVisible = false;
    camera.stop();
    if (ws) ws.close();
    clearInterval(timerInterval);
    document.removeEventListener("visibilitychange", handleVisibilityChange);
    
    log("Session ended.");
    monitorStatus.innerHTML = "Session Paused";

    // Calculate stats
    var durationMinutes = Math.floor((Date.now() - sessionStartTime) / 60000);
    var avgRecovery = 0;
    
    if (recoveryTimes.length > 0) {
        var sum = recoveryTimes.reduce(function(a, b) { return a + b; }, 0);
        avgRecovery = (sum / recoveryTimes.length).toFixed(1);
    }

    // Grade calculation
    var grades = ["F", "D-", "C", "B", "A+"];
    var comments = ["Disgraceful.", "Barely conscious.", "Mediocre.", "Not bad.", "Absolute machine."];
    var score = Math.max(0, 4 - Math.floor(roasts / 2));
    var grade = grades[score] || "F";

    // Save session to localStorage
    var STORAGE_KEY = "focusguard_sessions";
    var sessions = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    sessions.push({
        date: new Date().toISOString(),
        duration: durationMinutes,
        roasts: roasts,
        avgRecovery: parseFloat(avgRecovery),
        grade: grade
    });
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    
    saveActivityLog("[INFO] Session ended - Grade: " + grade, "info");

    // Show Report Card
    document.getElementById("reportCardStyle").style.display = "block";
    document.getElementById("rcDuration").textContent = focusTimerEl.textContent;
    document.getElementById("rcRoasts").textContent = roasts;
    if (recoveryRateEl) {
        document.getElementById("rcRecovery").textContent = avgRecovery + "s";
    }
    document.getElementById("rcVerdict").textContent = "Grade: " + grade + ". " + comments[score];
};

// =============================================================================
// Initialization
// =============================================================================

document.addEventListener("DOMContentLoaded", function() {
    settings = getSettings();
    var meshToggle = document.getElementById("meshToggle");
    if (meshToggle) {
        meshToggle.checked = settings.showMesh !== false;
    }
});
