DROP DATABASE IF EXISTS quartz;
CREATE DATABASE quartz;
USE quartz;

CREATE TABLE network_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    employee_id VARCHAR(50),
    agent_used VARCHAR(50),
    original_query TEXT,
    action VARCHAR(50),
    status VARCHAR(50),
    details TEXT,
    recommendation TEXT,
    vpn_access_level VARCHAR(50),
    duration VARCHAR(50),
    justification TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE time_entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    employee_id VARCHAR(50),
    agent_used VARCHAR(50),
    original_query TEXT,
    action VARCHAR(50),
    status VARCHAR(50),
    details TEXT,
    recommendation TEXT,
    time_correction VARCHAR(50),
    justification TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    employee_id VARCHAR(50),
    agent_used VARCHAR(50),
    original_query TEXT,
    action VARCHAR(50),
    status VARCHAR(50),
    details TEXT,
    recommendation TEXT,
    risk_level VARCHAR(50),
    justification TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE compliance_checks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    employee_id VARCHAR(50),
    agent_used VARCHAR(50),
    original_query TEXT,
    action VARCHAR(50),
    status VARCHAR(50),
    details TEXT,
    recommendation TEXT,
    violation_level VARCHAR(50),
    justification TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE decisions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    employee_id VARCHAR(50),
    decision VARCHAR(50),
    confidence INT,
    reason TEXT,
    recommendations TEXT,
    conditions TEXT,
    agent_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE monitored_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(100) NOT NULL,
    machine_id VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_check TIMESTAMP NULL,
    next_check TIMESTAMP NULL,
    monitoring_frequency INT DEFAULT 300,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_machine (employee_id, machine_id)
);

CREATE TABLE system_issues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(100) NOT NULL,
    machine_id VARCHAR(100),
    issue_type VARCHAR(50),
    severity VARCHAR(20),
    description TEXT,
    auto_resolved BOOLEAN DEFAULT FALSE,
    resolution TEXT,
    resolved_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL
);

CREATE TABLE monitoring_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(100) NOT NULL,
    machine_id VARCHAR(100),
    check_type VARCHAR(50),
    status VARCHAR(50),
    details TEXT,
    response_time_ms INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


INSERT INTO monitored_users (employee_id, machine_id, is_active) 
VALUES ('1212', 'PC-001', TRUE);

SELECT 'Database created successfully!' as message;
SHOW TABLES;