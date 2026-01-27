# FirewallWatch - Windows Firewall Monitor

A lightweight, containerized solution to monitor Windows Firewall status across multiple VMs.

![Dashboard Preview](frontend/public/preview_placeholder.png)

## Features
- **Real-time Dashboard**: View status of all monitored hosts.
- **Heartbeat Monitoring**: Agents send updates every 5 minutes.
- **Risk Detection**: Alerts if any Firewall Profile (Domain, Private, Public) is disabled.
- **Email Alerts**: Notification if an agent goes silent or reports risk.
- **Dark Mode**: Sleek UI built with Vue 3 and TailwindCSS.

## Project Structure
- `/backend`: FastAPI (Python) application.
- `/frontend`: Vue 3 + Vite application.
- `/agent`: PowerShell script for Windows VMs.

## Setup Instructions

### 1. Prerequisites
- Docker & Docker Compose
- Windows VM (for the agent)

### 2. Configure Environment
Create a `.env` file in the `backend/` directory:

```ini
API_KEY=your-secret-key
ALERT_TIMEOUT_MINUTES=10
ALERT_RECIPIENT_EMAIL=admin@example.com
ALERT_SENDER_EMAIL=alerts@example.com
# SMTP Settings (Example for Gmail)
SMTP_HOSTNAME=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=tapp password
```

### 3. Start the Server
Run the following command in the root directory:

```bash
docker-compose up --build -d
```

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000

### 4. Deploy Agent
On each Windows VM you want to monitor:

1. Copy the contents of `/agent` to the VM (e.g., `C:\FirewallMonitor`).
2. Edit `firewall_monitor.ps1`:
   - Update `$ServerUrl` to point to your Docker host IP (e.g., `http://192.168.1.100:8000/api/heartbeat`).
   - Update `$ApiKey` to match your `.env` file.
3. Open PowerShell as Administrator.
4. Run `install_task.ps1` to create the Scheduled Task.
   - Or run `.\firewall_monitor.ps1` manually to test.

## Development
- **Backend**: `cd backend && uvicorn main:app --reload`
- **Frontend**: `cd frontend && npm install && npm run dev`

## License
MIT
# CheckFirewall
