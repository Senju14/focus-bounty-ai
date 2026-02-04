/**
 * FocusGuard AI - Dashboard
 */

var STORAGE_KEY = "focusguard_sessions";
var LOG_KEY = "focusguard_logs";

// Load and display data
document.addEventListener("DOMContentLoaded", function() {
    loadDashboardData();
    loadActivityLog();
    
    // Setup event listeners
    var clearBtn = document.getElementById("clearHistoryBtn");
    if (clearBtn) {
        clearBtn.addEventListener("click", clearHistory);
    }
});

function loadDashboardData() {
    var sessions = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    
    // Calculate totals
    var totalMinutes = 0;
    var totalRoasts = 0;
    var totalRecovery = 0;
    var recoveryCount = 0;

    sessions.forEach(function(s) {
        totalMinutes += s.duration || 0;
        totalRoasts += s.roasts || 0;
        if (s.avgRecovery) {
            totalRecovery += s.avgRecovery;
            recoveryCount++;
        }
    });

    // Update stats
    var hours = Math.floor(totalMinutes / 60);
    var mins = totalMinutes % 60;
    document.getElementById("totalFocusTime").textContent = hours + "h " + mins + "m";
    document.getElementById("totalSessions").textContent = sessions.length;
    document.getElementById("totalRoasts").textContent = totalRoasts;
    document.getElementById("avgRecovery").textContent = recoveryCount > 0 
        ? (totalRecovery / recoveryCount).toFixed(1) + "s" 
        : "0s";

    // Render history
    renderHistory(sessions);
}

function renderHistory(sessions) {
    var container = document.getElementById("historyList");
    
    if (sessions.length === 0) {
        container.innerHTML = '<div class="empty-state">' +
            '<span class="empty-icon">--</span>' +
            '<p>No sessions recorded yet. Start focusing!</p>' +
            '</div>';
        return;
    }

    // Sort by date descending
    sessions.sort(function(a, b) { 
        return new Date(b.date) - new Date(a.date); 
    });

    var html = "";
    sessions.forEach(function(s) {
        var gradeClass = getGradeClass(s.grade);
        var date = new Date(s.date).toLocaleDateString("vi-VN", {
            weekday: "short",
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });

        html += '<div class="history-item">' +
            '<div>' +
            '<div class="history-date">' + date + '</div>' +
            '<div class="history-stats">' +
            '<span>' + (s.duration || 0) + 'm</span>' +
            '<span>' + (s.roasts || 0) + ' roasts</span>' +
            '</div>' +
            '</div>' +
            '<span class="grade-badge ' + gradeClass + '">' + (s.grade || "N/A") + '</span>' +
            '</div>';
    });
    container.innerHTML = html;
}

function getGradeClass(grade) {
    if (!grade) return "";
    if (grade.indexOf("A") !== -1) return "grade-a";
    if (grade.indexOf("B") !== -1) return "grade-b";
    if (grade.indexOf("C") !== -1) return "grade-c";
    if (grade.indexOf("D") !== -1) return "grade-d";
    return "grade-f";
}

function loadActivityLog() {
    var logs = JSON.parse(localStorage.getItem(LOG_KEY) || "[]");
    var container = document.getElementById("activityLog");

    if (logs.length === 0) {
        container.innerHTML = '<div class="empty-state">' +
            '<span class="empty-icon">--</span>' +
            '<p>Activity log will appear here after your sessions.</p>' +
            '</div>';
        return;
    }

    // Show last 50 logs
    var recentLogs = logs.slice(-50).reverse();
    
    var html = "";
    recentLogs.forEach(function(log) {
        var typeClass = log.type === "roast" ? "log-roast" : 
                       log.type === "praise" ? "log-praise" : "";
        html += '<div class="log-entry">' +
            '<span class="log-time">[' + log.time + ']</span>' +
            '<span class="' + typeClass + '">' + log.message + '</span>' +
            '</div>';
    });
    container.innerHTML = html;
}

function clearHistory() {
    if (confirm("Are you sure you want to clear all history? This cannot be undone.")) {
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem(LOG_KEY);
        loadDashboardData();
        loadActivityLog();
    }
}

// Export for use in app.js
window.FocusGuardDashboard = {
    saveSession: function(data) {
        var sessions = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
        sessions.push({
            date: new Date().toISOString(),
            duration: data.duration,
            roasts: data.roasts,
            avgRecovery: data.avgRecovery,
            grade: data.grade
        });
        localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    },
    
    addLog: function(message, type) {
        type = type || "info";
        var logs = JSON.parse(localStorage.getItem(LOG_KEY) || "[]");
        logs.push({
            time: new Date().toLocaleTimeString(),
            message: message,
            type: type
        });
        if (logs.length > 500) logs.shift();
        localStorage.setItem(LOG_KEY, JSON.stringify(logs));
    }
};
