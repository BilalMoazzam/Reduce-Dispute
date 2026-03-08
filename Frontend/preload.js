const { contextBridge, ipcRenderer } = require("electron");

const BASE_URL = "http://127.0.0.1:8001";

contextBridge.exposeInMainWorld("api", {
    getStatus: () =>
        fetch(`${BASE_URL}/status`).then(res => res.json()).catch(err => ({ error: err.message })),

    getAllData: () =>
        fetch(`${BASE_URL}/data`).then(res => res.json()).catch(err => ({ error: err.message })),

    getUsers: () =>
        fetch(`${BASE_URL}/users`).then(res => res.json()).catch(err => ({ error: err.message })),

    getDevices: () =>
        fetch(`${BASE_URL}/devices`).then(res => res.json()).catch(err => ({ error: err.message })),

    getDeviceData: (employeeId) =>
        fetch(`${BASE_URL}/device-data/${employeeId}`).then(res => res.json()).catch(err => ({ error: err.message })),

    getNetworkDevices: () =>
        fetch(`${BASE_URL}/network-devices`).then(res => res.json()).catch(err => ({ error: err.message })),

    onDeviceDiscovered: (callback) => {
        ipcRenderer.on('device-discovered', (event, device) => callback(device));
    },
    
    onDeviceLost: (callback) => {
        ipcRenderer.on('device-lost', (event, device) => callback(device));
    },
    
    getRemoteDeviceData: (ip, employeeId) => {
        return fetch(`http://${ip}:8001/device-data/${employeeId}`)
            .then(res => res.json())
            .catch(err => ({ error: 'Device offline: ' + err.message }));
    }
});