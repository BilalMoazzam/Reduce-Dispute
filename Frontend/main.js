const { app, BrowserWindow, Menu, ipcMain } = require("electron");
const path = require("path");
const bonjour = require('bonjour')();
const os = require('os');

let mainWindow;
let adminWindow;
let bonjourService = null;
let browser = null;

function getLocalIP() {
    const interfaces = os.networkInterfaces();
    for (const name of Object.keys(interfaces)) {
        for (const iface of interfaces[name]) {
            if (iface.family === 'IPv4' && !iface.internal) {
                return iface.address;
            }
        }
    }
    return '127.0.0.1';
}


function startBroadcasting() {
    const localIP = getLocalIP();

    function checkBackendAndBroadcast() {
        fetch('http://127.0.0.1:8001/status')
            .then(res => res.json())
            .then(status => {
                if (status && status.running) {
                    return fetch('http://127.0.0.1:8001/users');
                } else {
                    throw new Error('Backend not running');
                }
            })
            .then(res => res.json())
            .then(users => {
                const employeeName = users && users.length > 0 ? users[0].employee_id : 'unknown';

                if (bonjourService) {
                    bonjourService.stop();
                }

                bonjourService = bonjour.publish({
                    name: `Quartz-${os.hostname()}`,
                    type: 'quartz',
                    port: 8001,
                    txt: {
                        employee: employeeName,
                        machine: os.hostname(),
                        ip: localIP,
                        status: 'online'
                    }
                });

                console.log(`Broadcasting Quartz service as ${employeeName} on ${localIP}:8001 (backend online)`);
            })
            .catch(err => {
                console.log('Backend not available - stopping broadcast');
                if (bonjourService) {
                    bonjourService.stop();
                    bonjourService = null;
                }
            });
    }

    checkBackendAndBroadcast();
    setInterval(checkBackendAndBroadcast, 5000);
}

function monitorBackend() {
    let backendOnline = false;

    setInterval(() => {
        fetch('http://127.0.0.1:8001/status')
            .then(res => res.json())
            .then(status => {
                if (status && status.running) {
                    if (!backendOnline) {
                        console.log('✅ Backend came online');
                        backendOnline = true;
                    }
                } else {
                    if (backendOnline) {
                        console.log('❌ Backend went offline');
                        backendOnline = false;
                        if (bonjourService) {
                            bonjourService.stop();
                            bonjourService = null;
                        }
                    }
                }
            })
            .catch(() => {
                if (backendOnline) {
                    console.log('❌ Backend went offline');
                    backendOnline = false;
                    if (bonjourService) {
                        bonjourService.stop();
                        bonjourService = null;
                    }
                }
            });
    }, 3000);
}

function startDiscovery() {
    browser = bonjour.find({ type: 'quartz' });

    browser.on('up', (service) => {
        console.log('Found Quartz instance:', service.name);
        console.log('   - Employee:', service.txt.employee);
        console.log('   - Machine:', service.txt.machine);
        console.log('   - IP:', service.txt.ip);

        if (adminWindow) {
            adminWindow.webContents.send('device-discovered', {
                name: service.name,
                employee: service.txt.employee,
                machine: service.txt.machine,
                ip: service.txt.ip,
                port: service.port,
                addresses: service.addresses
            });
        }
    });

    browser.on('down', (service) => {
        console.log('🔌 Quartz instance went offline:', service.name);

        if (adminWindow) {
            adminWindow.webContents.send('device-lost', {
                name: service.name,
                ip: service.txt?.ip
            });
        }
    });

    browser.start();
}

function createMainWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
            contextIsolation: true,
            nodeIntegration: false
        },
        title: 'Quartz AI - Local Monitor'
    });

    mainWindow.loadFile("index.html");

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

function createAdminWindow() {
    adminWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
            contextIsolation: true,
            nodeIntegration: false
        },
        title: 'Quartz AI - Admin Dashboard'
    });

    adminWindow.loadFile("admin-dashboard.html");

    adminWindow.on('closed', () => {
        adminWindow = null;
    });
}

const menu = Menu.buildFromTemplate([
    {
        label: 'File',
        submenu: [
            {
                label: 'Open Local Monitor',
                click: () => {
                    if (!mainWindow) createMainWindow();
                    else mainWindow.focus();
                }
            },
            {
                label: 'Open Admin Dashboard',
                click: () => {
                    if (!adminWindow) createAdminWindow();
                    else adminWindow.focus();
                }
            },
            { type: 'separator' },
            { role: 'quit' }
        ]
    },
    {
        label: 'Network',
        submenu: [
            {
                label: 'Refresh Discovery',
                click: () => {
                    if (browser) {
                        browser.update();
                    }
                }
            }
        ]
    }
]);

Menu.setApplicationMenu(menu);

app.whenReady().then(() => {
    monitorBackend();
    startBroadcasting();
    startDiscovery();
    createAdminWindow();
});

app.on('window-all-closed', () => {
    if (bonjourService) {
        bonjourService.stop();
    }
    if (browser) {
        browser.stop();
    }
    bonjour.destroy();

    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createAdminWindow();
    }
});