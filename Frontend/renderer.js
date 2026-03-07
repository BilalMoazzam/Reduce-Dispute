const REFRESH_INTERVAL = 1000;
let refreshTimer;

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getSummary(type, data) {
    if (!data || data.error) return {};

    switch (type) {
        case 'network':
            return {
                'Internet': data.internet_connected ? '<span class="dot-green"></span>Connected' : '<span class="dot-red"></span>Disconnected',
                'VPN': data.vpn_connected ? '<span class="dot-green"></span>Connected' : '<span class="dot-red"></span>Disconnected',
                'Method': data.connection_method || 'N/A',
                'Gateway': data.gateway || 'N/A',
                'Latency (Google)': data.connectivity_tests?.['Google HTTP']?.latency_ms?.toFixed(2) + ' ms' || 'N/A'
            };
        case 'health':
            return {
                'CPU': data.cpu?.percent?.toFixed(1) + '%' || 'N/A',
                'Memory': data.memory?.percent?.toFixed(1) + '%' || 'N/A',
                'Disk (C:)': data.disk?.[0]?.percent?.toFixed(1) + '%' || 'N/A',
                'Processes': data.processes?.total || 'N/A'
            };
        case 'activity':
            return {
                'Total Processes': data.total_processes || 'N/A',
                'User Apps': data.user_processes || 'N/A',
                'Resource Hogs': data.resource_hogs?.length || 0,
                'Suspicious': data.suspicious_processes?.length || 0
            };
        case 'vpn':
            return {
                'VPN Connected': data.network_status?.vpn_connected ? '<span class="dot-green"></span>Yes' : '<span class="dot-red"></span>No',
                'Internet': data.network_status?.internet_connected ? '<span class="dot-green"></span>Yes' : '<span class="dot-red"></span>No',
                'Policy': data.policy_requirements?.substring(0, 30) + '…' || 'N/A'
            };
        case 'timekeeper':
            return {
                'Shift': data.expected_shift || 'N/A',
                'Events Today': data.actual_clock_events?.length || 0,
                'Current Time': data.current_time ? new Date(data.current_time).toLocaleTimeString() : 'N/A'
            };
        case 'compliance':
            return {
                'Employee': data.employee_id || 'N/A',
                'Rules Count': data.policy_rules?.length || 0,
                'Action': data.action_description || 'N/A'
            };
        case 'anomaly':
            return {
                'Historical Patterns': data.historical_patterns?.length || 0,
                'Network Status': data.network_status?.internet_connected ? '<span class="dot-green"></span>OK' : '<span class="dot-red"></span>Issue',
                'System Health Issues': data.system_health?.issues?.length || 0
            };
        default:
            return { 'Data available': 'Yes' };
    }
}

function createCard(type, data) {
    const card = document.createElement('div');
    card.className = 'card';

    const header = document.createElement('div');
    header.className = 'card-header';
    header.innerHTML = `<h3>${type.charAt(0).toUpperCase() + type.slice(1)}</h3>`;

    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'summary';

    if (data.error) {
        summaryDiv.innerHTML = `<div class="error">Error: ${data.error}</div>`;
    } else {
        const summary = getSummary(type, data);
        let summaryHtml = '';
        for (const [key, value] of Object.entries(summary)) {
            summaryHtml += `<div class="summary-item"><span class="label">${key}:</span> <span class="value">${value}</span></div>`;
        }
        summaryDiv.innerHTML = summaryHtml;
    }

    card.appendChild(header);
    card.appendChild(summaryDiv);

    return card;
}

async function updateStatus() {
    try {
        const status = await window.api.getStatus();
        const indicator = document.getElementById('serviceStatus');
        const statusText = document.getElementById('statusText');
        if (status && status.running) {
            indicator.style.color = '#22c55e';
            statusText.textContent = 'Running';
        } else {
            indicator.style.color = '#ef4444';
            statusText.textContent = 'Stopped';
        }
    } catch (err) {
        console.error('Status fetch failed:', err);
        document.getElementById('serviceStatus').style.color = '#ef4444';
        document.getElementById('statusText').textContent = 'Offline';
    }
}

async function loadMachineInfo() {
    try {
        const users = await window.api.getUsers();
        if (users && users.length > 0) {
            const user = users[0];
            document.getElementById('employeeId').textContent = `Employee ID: ${user.employee_id || 'N/A'}`;
            document.getElementById('machineId').textContent = `Machine ID: ${user.machine_id || 'N/A'}`;
            document.getElementById('machineName').textContent = `Machine Name: ${user.machine_name || user.machine_id || 'N/A'}`;
            document.getElementById('userName').textContent = `User Name: ${user.employee_id || 'N/A'}`;
        } else {
            document.getElementById('employeeId').textContent = 'Employee ID: N/A';
            document.getElementById('machineId').textContent = 'Machine ID: N/A';
            document.getElementById('machineName').textContent = 'Machine Name: N/A';
            document.getElementById('userName').textContent = 'User Name: N/A';
        }
    } catch (err) {
        console.error('Failed to load machine info:', err);
        document.getElementById('employeeId').textContent = 'Employee ID: Error';
        document.getElementById('machineId').textContent = 'Machine ID: Error';
        document.getElementById('machineName').textContent = 'Machine Name: Error';
        document.getElementById('userName').textContent = 'User Name: Error';
    }
}

async function loadData() {
    try {
        const data = await window.api.getAllData();
        const container = document.getElementById('dashboard');
        container.innerHTML = '';

        if (!data || Object.keys(data).length === 0) {
            container.innerHTML = '<div class="empty">No monitoring data available yet.</div>';
            return;
        }

        for (const [type, typeData] of Object.entries(data)) {
            const card = createCard(type, typeData);
            container.appendChild(card);
        }

        document.getElementById('lastUpdated').textContent = 'Last updated: ' + new Date().toLocaleString();
    } catch (err) {
        console.error('Data fetch failed:', err);
        document.getElementById('dashboard').innerHTML = '<div class="error">Failed to load data. Is the backend running?</div>';
    }
}

async function refreshAll() {
    const btn = document.getElementById('refreshBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '↻ Refreshing...';
    btn.disabled = true;
    try {
        await updateStatus();
        await loadMachineInfo();
        await loadData();
    } catch (err) {
        console.error('Refresh failed:', err);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

function startAutoRefresh() {
    refreshAll();
    refreshTimer = setInterval(refreshAll, REFRESH_INTERVAL);
}

function stopAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer);
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('refreshBtn').addEventListener('click', refreshAll);
    startAutoRefresh();
});

window.addEventListener('beforeunload', stopAutoRefresh);