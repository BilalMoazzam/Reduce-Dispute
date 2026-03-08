const REFRESH_INTERVAL = 3000;
let refreshTimer;
let currentDeviceData = {};
let devicesList = [];
let discoveredDevices = [];
let localDevices = [];
let statusChart = null;
let activityChart = null;

console.log('Admin renderer loaded');
console.log('API available:', window.api);

const originalLog = console.log;
console.log = function (...args) {
    originalLog.apply(console, ['[Admin]', ...args]);
};

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
                'Internet': data.internet_connected ?
                    '<span class="dot-green"></span>Connected' :
                    '<span class="dot-red"></span>Disconnected',
                'VPN': data.vpn_connected ?
                    '<span class="dot-green"></span>Connected' :
                    '<span class="dot-red"></span>Disconnected',
                'Method': data.connection_method || 'N/A',
                'Gateway': data.gateway || 'N/A',
                'Latency': data.connectivity_tests?.['Google HTTP']?.latency_ms?.toFixed(2) + ' ms' || 'N/A'
            };
        case 'health':
            return {
                'CPU': (data.cpu?.percent?.toFixed(1) || '0') + '%',
                'Memory': (data.memory?.percent?.toFixed(1) || '0') + '%',
                'Disk (C:)': (data.disk?.[0]?.percent?.toFixed(1) || '0') + '%',
                'Processes': data.processes?.total || '0'
            };
        case 'activity':
            return {
                'Total Processes': data.total_processes || '0',
                'User Apps': data.user_processes || '0',
                'Resource Hogs': data.resource_hogs?.length || 0,
                'Suspicious': data.suspicious_processes?.length || 0
            };
        case 'vpn':
            return {
                'VPN Connected': data.network_status?.vpn_connected ?
                    '<span class="dot-green"></span>Yes' :
                    '<span class="dot-red"></span>No',
                'Internet': data.network_status?.internet_connected ?
                    '<span class="dot-green"></span>Yes' :
                    '<span class="dot-red"></span>No',
                'Policy': data.policy_requirements?.substring(0, 25) + '…' || 'N/A'
            };
        case 'timekeeper':
            return {
                'Shift': data.expected_shift || 'N/A',
                'Events Today': data.actual_clock_events?.length || 0,
                'Current Time': data.current_time ?
                    new Date(data.current_time).toLocaleTimeString() : 'N/A'
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
                'Network Status': data.network_status?.internet_connected ?
                    '<span class="dot-green"></span>OK' :
                    '<span class="dot-red"></span>Issue',
                'Health Issues': data.system_health?.issues?.length || 0
            };
        default:
            return { 'Data': 'Available' };
    }
}

function createCard(type, data) {
    const card = document.createElement('div');
    card.className = 'card';

    const header = document.createElement('div');
    header.className = 'card-header';
    header.setAttribute('data-type', type);
    header.innerHTML = `<h3>${type.charAt(0).toUpperCase() + type.slice(1)}</h3>`;

    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'summary';

    if (data.error) {
        summaryDiv.innerHTML = `<div class="error">Error: ${data.error}</div>`;
    } else {
        const summary = getSummary(type, data);
        let summaryHtml = '';
        for (const [key, value] of Object.entries(summary)) {
            summaryHtml += `<div class="summary-item">
                <span class="label">${key}:</span> 
                <span class="value">${value}</span>
            </div>`;
        }
        summaryDiv.innerHTML = summaryHtml;
    }

    card.appendChild(header);
    card.appendChild(summaryDiv);
    return card;
}

function createDeviceCard(device) {
    const card = document.createElement('div');
    card.className = `device-card ${device.status}`;

    const lastSeen = device.last_seen ?
        new Date(device.last_seen).toLocaleString() : 'Never';
    const statusText = device.status === 'online' ? 'ONLINE' : 'OFFLINE';
    const statusClass = device.status === 'online' ? 'status-online' : 'status-offline';
    const employeeName = device.employee_id || 'Unknown';
    const machineId = device.machine_id || 'Unknown';
    const ipAddress = device.ip_address || 'Unknown';
    const source = device.remote ? 'Network Discovery' : 'Database';
    
    card.setAttribute('data-employee-id', employeeName);
    card.setAttribute('data-machine-id', machineId);
    card.setAttribute('data-ip', ipAddress);
    card.setAttribute('data-remote', device.remote || false);

    card.innerHTML = `
        <div class="device-header">
            <span class="device-name">${machineId}</span>
            <span class="device-status ${statusClass}">${statusText}</span>
        </div>
        <div class="device-details">
            <div class="detail-row">
                <span class="detail-label">👤 Employee:</span>
                <span class="detail-value">${employeeName}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">🆔 Machine ID:</span>
                <span class="detail-value">${machineId}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">🌐 IP Address:</span>
                <span class="detail-value">${ipAddress}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">📡 Source:</span>
                <span class="detail-value">${source}</span>
            </div>
        </div>
        <div class="device-footer">
            <span class="last-seen">🕐 ${lastSeen}</span>
            <button class="view-details-btn">View Details →</button>
        </div>
    `;

    const viewBtn = card.querySelector('.view-details-btn');
    viewBtn.addEventListener('click', function (event) {
        event.preventDefault();
        event.stopPropagation();
        const empId = card.getAttribute('data-employee-id');
        console.log('View Details clicked:', empId);
        if (typeof window.showDeviceDetails === 'function') {
            window.showDeviceDetails(empId);
        }
    });

    card.addEventListener('click', function (event) {
        if (!event.target.classList.contains('view-details-btn')) {
            const empId = card.getAttribute('data-employee-id');
            console.log('Card clicked:', empId);
            if (typeof window.showDeviceDetails === 'function') {
                window.showDeviceDetails(empId);
            }
        }
    });

    return card;
}

function updateCharts() {
    const online = devicesList.filter(d => d.status === 'online').length;
    const offline = devicesList.filter(d => d.status === 'offline').length;

    if (statusChart) {
        statusChart.destroy();
    }

    const statusCtx = document.getElementById('statusChart').getContext('2d');
    statusChart = new Chart(statusCtx, {
        type: 'doughnut',
        data: {
            labels: ['Online', 'Offline'],
            datasets: [{
                data: [online, offline],
                backgroundColor: ['#22c55e', '#ef4444'],
                borderColor: ['#1e293b', '#1e293b'],
                borderWidth: 3,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#94a3b8',
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1
                }
            },
            cutout: '60%'
        }
    });

    if (activityChart) {
        activityChart.destroy();
    }

    const activityCtx = document.getElementById('activityChart').getContext('2d');
    activityChart = new Chart(activityCtx, {
        type: 'bar',
        data: {
            labels: devicesList.slice(0, 5).map(d => d.machine_name || d.machine_id),
            datasets: [{
                label: 'Active Time (minutes)',
                data: devicesList.slice(0, 5).map(() => Math.floor(Math.random() * 60) + 15),
                backgroundColor: '#38bdf8',
                borderRadius: 6,
                hoverBackgroundColor: '#60a5fa'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94a3b8', font: { size: 12 } }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#334155' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        color: '#94a3b8',
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
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

async function checkDatabaseStatus() {
    try {
        const users = await window.api.getUsers();
        const dbStatus = document.getElementById('dbStatus');
        const dbStatusText = document.getElementById('dbStatusText');
        const dbDetails = document.getElementById('dbDetails');
        const dbDiv = document.querySelector('.database-status');

        if (users && !users.error) {
            dbStatus.className = 'online';
            dbStatusText.innerHTML = 'Database: <span style="color:#22c55e">Connected</span>';
            dbDetails.textContent = `(${users.length} users)`;
            dbDiv.classList.add('online');
            dbDiv.classList.remove('offline');
        } else {
            dbStatus.className = 'offline';
            dbStatusText.innerHTML = 'Database: <span style="color:#ef4444">Offline</span>';
            dbDetails.textContent = '(using network discovery only)';
            dbDiv.classList.add('offline');
            dbDiv.classList.remove('online');
        }
    } catch (err) {
        console.error('Database check failed:', err);
        document.getElementById('dbStatus').className = 'offline';
        document.getElementById('dbStatusText').innerHTML = 'Database: <span style="color:#ef4444">Offline</span>';
        document.getElementById('dbDetails').textContent = '(connection failed)';
    }
}

async function loadDevices() {
    try {
        let backendOnline = false;
        try {
            const status = await window.api.getStatus();
            backendOnline = status && status.running;
        } catch (err) {
            console.log('Backend is offline');
        }

        localDevices = [];
        if (backendOnline) {
            try {
                const response = await window.api.getDevices();
                if (response && !response.error) {
                    localDevices = response;
                    console.log('Local devices:', localDevices);
                }
            } catch (err) {
                console.error('Failed to get local devices:', err);
            }
        }

        discoveredDevices = discoveredDevices.map(device => {
            if (!backendOnline) {
                return { ...device, status: 'offline' };
            }
            return device;
        });

        const allDevices = [];
        const seen = new Set();

        localDevices.forEach(device => {
            const key = `${device.employee_id}:${device.machine_id}`;
            if (!seen.has(key)) {
                seen.add(key);
                allDevices.push({
                    ...device,
                    local: true,
                    remote: false,
                    source: 'local',
                    status: backendOnline ? device.status : 'offline'
                });
            }
        });

        discoveredDevices.forEach(device => {
            const exists = allDevices.some(d =>
                d.machine_id === device.machine_id ||
                d.ip_address === device.ip_address
            );
            if (!exists) {
                allDevices.push(device);
            }
        });

        devicesList = allDevices;
        updateUI();
    } catch (err) {
        console.error('Devices fetch failed:', err);
    }
}

function updateUI() {
    const online = devicesList.filter(d => d.status === 'online').length;
    const offline = devicesList.filter(d => d.status === 'offline').length;

    document.getElementById('totalDevices').textContent = devicesList.length;
    document.getElementById('onlineDevices').textContent = online;
    document.getElementById('offlineDevices').textContent = offline;

    const discoveredCount = document.getElementById('discoveredCount');
    if (discoveredCount) {
        discoveredCount.textContent = `(${discoveredDevices.length} found)`;
    }

    const grid = document.getElementById('deviceGrid');
    if (!grid) return;

    if (devicesList.length === 0) {
        grid.innerHTML = '<div class="empty">📭 No devices found</div>';
    } else {
        grid.innerHTML = '';
        devicesList.forEach(device => {
            grid.appendChild(createDeviceCard(device));
        });
    }

    const select = document.getElementById('deviceSelect');
    if (select) {
        select.innerHTML = '<option value="">-- Choose a device --</option>';
        devicesList.forEach(device => {
            const option = document.createElement('option');
            option.value = device.employee_id || device.machine_id;
            option.textContent = `${device.machine_name || device.machine_id} - ${device.status}`;
            option.style.color = device.status === 'online' ? '#22c55e' : '#ef4444';
            select.appendChild(option);
        });
    }

    if (typeof updateCharts === 'function') {
        updateCharts();
    }
}

async function showDeviceDetails(employeeId) {
    if (!employeeId) {
        console.error('No employee ID provided');
        return;
    }

    console.log('showDeviceDetails called with:', employeeId);

    try {
        const device = devicesList.find(d => 
            d.employee_id === employeeId || d.machine_id === employeeId
        );

        if (!device) {
            console.error('Device not found:', employeeId);
            document.getElementById('deviceDashboard').innerHTML = 
                '<div class="error">Device not found</div>';
            return;
        }

        console.log('Found device:', device);

        const infoBar = document.getElementById('selectedDeviceInfo');
        if (infoBar) {
            document.getElementById('selectedDeviceName').textContent = 
                device.machine_name || device.machine_id;
            document.getElementById('selectedDeviceStatus').innerHTML = 
                device.status === 'online' ? 
                '<span class="dot-green"></span>Online' : 
                '<span class="dot-red"></span>Offline';
            document.getElementById('selectedDeviceLastSeen').textContent = 
                device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never';
            document.getElementById('selectedDeviceIP').textContent = 
                device.ip_address || 'Unknown';
            infoBar.style.display = 'grid';
        }

        document.getElementById('toggleDevices').classList.remove('active');
        document.getElementById('toggleDetails').classList.add('active');
        document.getElementById('devicesView').classList.remove('active');
        document.getElementById('detailsView').classList.add('active');

        const select = document.getElementById('deviceSelect');
        if (select) {
            select.value = employeeId;
        }

        const container = document.getElementById('deviceDashboard');
        container.innerHTML = '<div class="loading">Loading device data...</div>';

        let data = {};
        if (device.remote) {
            data = await window.api.getRemoteDeviceData(device.ip_address, employeeId);
        } else {
            data = await window.api.getDeviceData(employeeId);
        }

        console.log('Device data received:', data);
        container.innerHTML = '';

        if (!data || data.error) {
            container.innerHTML = '<div class="empty">No monitoring data available</div>';
            return;
        }

        let hasData = false;
        for (const [type, typeData] of Object.entries(data)) {
            if (typeData && typeof typeData === 'object') {
                const card = createCard(type, typeData);
                container.appendChild(card);
                hasData = true;
            }
        }

        if (!hasData) {
            container.innerHTML = '<div class="empty">No monitoring data available</div>';
        }

    } catch (err) {
        console.error('Error in showDeviceDetails:', err);
        document.getElementById('deviceDashboard').innerHTML = 
            '<div class="error">Error: ' + err.message + '</div>';
    }
}

window.showDeviceDetails = showDeviceDetails;

async function refreshAll() {
    const btn = document.getElementById('refreshBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="btn-icon">⟳</span> Refreshing...';
    btn.disabled = true;

    try {
        await updateStatus();
        await checkDatabaseStatus();
        await loadDevices();

        const activeTab = document.querySelector('.view-container.active');
        if (activeTab && activeTab.id === 'detailsView') {
            const selectedDevice = document.getElementById('deviceSelect').value;
            if (selectedDevice) {
                await showDeviceDetails(selectedDevice);
            }
        }

        document.getElementById('lastUpdated').textContent =
            'Last updated: ' + new Date().toLocaleString();
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

if (window.api && window.api.onDeviceDiscovered) {
    window.api.onDeviceDiscovered((device) => {
        console.log('New device discovered:', device);
        const exists = discoveredDevices.some(d =>
            d.ip_address === device.ip || d.machine_id === device.machine
        );
        if (!exists) {
            discoveredDevices.push({
                employee_id: device.employee || device.machine,
                machine_id: device.machine,
                machine_name: device.name,
                last_seen: new Date().toISOString(),
                status: 'online',
                ip_address: device.ip,
                remote: true,
                source: 'discovery'
            });
            loadDevices();
        }
    });

    window.api.onDeviceLost((device) => {
        console.log('Device lost:', device);
        discoveredDevices = discoveredDevices.map(d => {
            if (d.ip_address === device.ip) {
                return { ...d, status: 'offline' };
            }
            return d;
        });
        loadDevices();
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const toggleDevices = document.getElementById('toggleDevices');
    const toggleDetails = document.getElementById('toggleDetails');
    const devicesView = document.getElementById('devicesView');
    const detailsView = document.getElementById('detailsView');
    const refreshBtn = document.getElementById('refreshBtn');
    const deviceSelect = document.getElementById('deviceSelect');

    if (toggleDevices) {
        toggleDevices.addEventListener('click', () => {
            toggleDevices.classList.add('active');
            toggleDetails.classList.remove('active');
            devicesView.classList.add('active');
            detailsView.classList.remove('active');
            loadDevices();
        });
    }

    if (toggleDetails) {
        toggleDetails.addEventListener('click', () => {
            const selectedDevice = deviceSelect ? deviceSelect.value : null;
            if (selectedDevice) {
                toggleDevices.classList.remove('active');
                toggleDetails.classList.add('active');
                devicesView.classList.remove('active');
                detailsView.classList.add('active');
                showDeviceDetails(selectedDevice);
            } else {
                alert('Please select a device first');
            }
        });
    }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshAll);
    }

    if (deviceSelect) {
        deviceSelect.addEventListener('change', (e) => {
            if (e.target.value) {
                showDeviceDetails(e.target.value);
            } else {
                const infoBar = document.getElementById('selectedDeviceInfo');
                if (infoBar) {
                    infoBar.style.display = 'none';
                }
                const dashboard = document.getElementById('deviceDashboard');
                if (dashboard) {
                    dashboard.innerHTML = '';
                }
            }
        });
    }

    window.showDeviceDetails = showDeviceDetails;
    startAutoRefresh();
});

window.addEventListener('beforeunload', stopAutoRefresh);