const { exec } = require('child_process');
const path = require('path');

console.log('Starting Quartz AI Backend...');

const backend = exec('python -m uvicorn service:app --port 8001', {
    cwd: path.join(__dirname, 'backend')
});

backend.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
});

setTimeout(() => {
    console.log('Starting Admin Dashboard...');
    const frontend = exec('npm start', {
        cwd: path.join(__dirname, 'frontend'),
        env: { ...process.env, ELECTRON_START_URL: 'file://' + path.join(__dirname, 'frontend/admin-dashboard.html') }
    });
    
    frontend.stdout.on('data', (data) => {
        console.log(`Frontend: ${data}`);
    });
}, 3000);

console.log('Launch script running. Press Ctrl+C to stop all services.');