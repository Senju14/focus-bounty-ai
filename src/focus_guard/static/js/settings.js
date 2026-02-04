/**
 * FocusGuard AI - Settings
 */

var SETTINGS_KEY = "focusguard_settings";

// Default settings
var defaultSettings = {
    voiceType: "auto",
    voiceLanguage: "en-US",
    speechRate: 1.1,
    voicePitch: 1.0,
    showMesh: true,
    tabDetection: true,
    playSiren: true,
    showWarningVideo: false,
    roastCooldown: 12,
    browserNotifications: true
};

// Load settings on page load
document.addEventListener("DOMContentLoaded", function() {
    loadSettings();
    
    // Setup event listeners
    var speechRateInput = document.getElementById("speechRate");
    var voicePitchInput = document.getElementById("voicePitch");
    
    speechRateInput.addEventListener("input", function(e) {
        document.getElementById("speechRateValue").textContent = e.target.value + "x";
        saveSettings();
    });
    
    voicePitchInput.addEventListener("input", function(e) {
        document.getElementById("voicePitchValue").textContent = e.target.value;
        saveSettings();
    });
    
    // Add change listeners to all inputs
    var inputs = document.querySelectorAll("select, input[type='checkbox'], input[type='number']");
    inputs.forEach(function(input) {
        input.addEventListener("change", saveSettings);
    });
    
    // Button listeners
    var requestNotifBtn = document.getElementById("requestNotificationBtn");
    if (requestNotifBtn) {
        requestNotifBtn.addEventListener("click", requestNotificationPermission);
    }
    
    var testVoiceBtn = document.getElementById("testVoiceBtn");
    if (testVoiceBtn) {
        testVoiceBtn.addEventListener("click", testVoice);
    }
    
    var testNotifBtn = document.getElementById("testNotificationBtn");
    if (testNotifBtn) {
        testNotifBtn.addEventListener("click", testNotification);
    }
    
    var testVideoBtn = document.getElementById("testVideoBtn");
    if (testVideoBtn) {
        testVideoBtn.addEventListener("click", testWarningVideo);
    }
    
    var closeVideoBtn = document.getElementById("closeVideoBtn");
    if (closeVideoBtn) {
        closeVideoBtn.addEventListener("click", closeWarningVideo);
    }
});

function loadSettings() {
    var saved = JSON.parse(localStorage.getItem(SETTINGS_KEY)) || defaultSettings;
    
    // Apply to UI
    document.getElementById("voiceType").value = saved.voiceType || defaultSettings.voiceType;
    document.getElementById("voiceLanguage").value = saved.voiceLanguage || defaultSettings.voiceLanguage;
    document.getElementById("speechRate").value = saved.speechRate || defaultSettings.speechRate;
    document.getElementById("voicePitch").value = saved.voicePitch || defaultSettings.voicePitch;
    document.getElementById("showMesh").checked = saved.showMesh !== false;
    document.getElementById("tabDetection").checked = saved.tabDetection !== false;
    document.getElementById("playSiren").checked = saved.playSiren !== false;
    document.getElementById("showWarningVideo").checked = saved.showWarningVideo === true;
    document.getElementById("roastCooldown").value = saved.roastCooldown || defaultSettings.roastCooldown;
    document.getElementById("browserNotifications").checked = saved.browserNotifications !== false;
    
    // Update display values
    document.getElementById("speechRateValue").textContent = saved.speechRate + "x";
    document.getElementById("voicePitchValue").textContent = saved.voicePitch;
}

function saveSettings() {
    var settings = {
        voiceType: document.getElementById("voiceType").value,
        voiceLanguage: document.getElementById("voiceLanguage").value,
        speechRate: parseFloat(document.getElementById("speechRate").value),
        voicePitch: parseFloat(document.getElementById("voicePitch").value),
        showMesh: document.getElementById("showMesh").checked,
        tabDetection: document.getElementById("tabDetection").checked,
        playSiren: document.getElementById("playSiren").checked,
        showWarningVideo: document.getElementById("showWarningVideo").checked,
        roastCooldown: parseInt(document.getElementById("roastCooldown").value),
        browserNotifications: document.getElementById("browserNotifications").checked
    };
    
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    showSaveStatus();
}

function showSaveStatus() {
    var status = document.getElementById("saveStatus");
    status.classList.add("show");
    setTimeout(function() { status.classList.remove("show"); }, 2000);
}

function requestNotificationPermission() {
    if ("Notification" in window) {
        Notification.requestPermission().then(function(permission) {
            if (permission === "granted") {
                new Notification("FocusGuard AI", {
                    body: "Notifications enabled! The Toxic Coach is watching.",
                    icon: "/static/assets/icon.png"
                });
            } else {
                alert("Notification permission denied. Enable it in browser settings.");
            }
        });
    } else {
        alert("Your browser does not support notifications.");
    }
}

function testVoice() {
    var settings = JSON.parse(localStorage.getItem(SETTINGS_KEY)) || defaultSettings;
    var voices = window.speechSynthesis.getVoices();
    
    var testPhrases = [
        "Hey! Get back to work, slacker!",
        "I'm watching you... always watching.",
        "Focus mode activated. No escape.",
        "Your productivity depends on me now."
    ];
    
    var utterance = new SpeechSynthesisUtterance(
        testPhrases[Math.floor(Math.random() * testPhrases.length)]
    );
    
    // Find voice based on settings
    var targetVoice = null;
    var lang = settings.voiceLanguage || "en-US";
    
    if (settings.voiceType === "female-young" || settings.voiceType === "female-mature") {
        targetVoice = voices.find(function(v) { 
            return v.lang.startsWith(lang.split("-")[0]) && 
                (v.name.toLowerCase().indexOf("female") !== -1 || 
                 v.name.indexOf("Zira") !== -1 || 
                 v.name.indexOf("Samantha") !== -1 ||
                 v.name.toLowerCase().indexOf("woman") !== -1);
        });
    } else if (settings.voiceType === "male-young" || settings.voiceType === "male-mature") {
        targetVoice = voices.find(function(v) { 
            return v.lang.startsWith(lang.split("-")[0]) && 
                (v.name.toLowerCase().indexOf("male") !== -1 || 
                 v.name.indexOf("David") !== -1 || 
                 v.name.indexOf("Mark") !== -1 ||
                 v.name.toLowerCase().indexOf("man") !== -1);
        });
    }
    
    // Fallback to language match
    if (!targetVoice) {
        targetVoice = voices.find(function(v) { return v.lang === lang; }) || 
                      voices.find(function(v) { return v.lang.startsWith(lang.split("-")[0]); }) ||
                      voices[0];
    }
    
    utterance.voice = targetVoice;
    utterance.rate = settings.speechRate || 1.1;
    utterance.pitch = settings.voicePitch || 1.0;
    
    // Adjust pitch for voice types
    if (settings.voiceType === "female-young" || settings.voiceType === "male-young") {
        utterance.pitch *= 1.2;
    } else if (settings.voiceType === "female-mature" || settings.voiceType === "male-mature") {
        utterance.pitch *= 0.85;
    } else if (settings.voiceType === "robotic") {
        utterance.pitch = 0.5;
        utterance.rate = 0.9;
    }
    
    window.speechSynthesis.speak(utterance);
}

function testNotification() {
    if ("Notification" in window && Notification.permission === "granted") {
        var notification = new Notification("FocusGuard Alert!", {
            body: "This is a test notification. Click to return to focus!",
            icon: "/static/assets/icon.png",
            tag: "focusguard-test",
            requireInteraction: true
        });
        
        notification.onclick = function() {
            window.focus();
            window.location.href = "/app";
            notification.close();
        };
    } else {
        alert("Please enable notifications first!");
    }
}

function testWarningVideo() {
    showWarningVideo();
}

function showWarningVideo() {
    var modal = document.getElementById("warningVideoModal");
    var video = document.getElementById("warningVideo");
    modal.classList.add("active");
    video.currentTime = 0;
    video.play().catch(function() {
        console.log("Warning video not found");
    });
}

function closeWarningVideo() {
    var modal = document.getElementById("warningVideoModal");
    var video = document.getElementById("warningVideo");
    modal.classList.remove("active");
    video.pause();
}

// Export settings getter for other pages
window.FocusGuardSettings = {
    get: function() {
        return JSON.parse(localStorage.getItem(SETTINGS_KEY)) || defaultSettings;
    }
};
