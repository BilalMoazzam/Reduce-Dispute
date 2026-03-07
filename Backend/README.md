# Quartz 2.0 - Complete Project

## Project Structure

```
quartz_complete/
├── agents/              # All AI agents
│   ├── coordinator.py   # Routes requests
│   ├── network.py       # Network & VPN checks
│   ├── timekeeper.py    # Time entries
│   ├── activity.py      # App monitoring
│   ├── compliance.py    # Labor law checks
│   └── decision.py      # Final decisions
├── models/              # LLM models
│   └── azure_llm.py     # Azure OpenAI wrapper
├── tools/               # Utilities
│   └── database.py      # MySQL integration
├── config/              # Configuration
│   └── .env.template    # Environment template
├── sql/                 # Database scripts
│   └── setup.sql        # Create tables
├── main.py              # Main orchestrator
├── requirements.txt     # Python dependencies
└── setup.sh             # Setup script
```

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp config/.env.template .env
nano .env
```

Add your credentials:
```
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
DB_PASSWORD=your_mysql_password
```

### 3. Setup Database
```bash
mysql -u root -p < sql/setup.sql
```

Or run manually in MySQL Workbench:
- Open `sql/setup.sql`
- Execute all queries

## Usage

Run single command:
```bash
python main.py "vpn not connecting" EMP121212
```

### Examples

```bash
python main.py "my time is wrong should be 9am" EMP001

python main.py "check network connection" EMP002

python main.py "missed break today" EMP003

python main.py "clock in at 9am but system shows 10am" EMP004
```

## How It Works

1. **Parse Input** - Coordinator determines which agent to use
2. **Run Agent** - Specific agent processes the request
3. **Save to MySQL** - Data saved to appropriate table
4. **Make Decision** - Decision agent provides final ruling
5. **Save Decision** - Decision saved to database

## MySQL Tables

- **network_logs** - VPN, connection, timeout data
- **time_entries** - Clock in/out disputes
- **activity_logs** - Application usage
- **compliance_checks** - Break violations, overtime
- **decisions** - Final approve/deny/escalate decisions

## View Data

```sql
USE quartz;
SELECT * FROM decisions ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM time_entries WHERE employee_id = 'EMP001';
SELECT * FROM network_logs WHERE vpn_connected = FALSE;
```

## Notes

- No need to run Google ADK manually
- Just run `main.py` with your query
- Everything auto-routes and saves to database
- Simple, clean, no comments in code
