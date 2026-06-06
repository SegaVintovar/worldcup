#!/bin/bash
# =============================================================================
# setup.sh — sq.codam.nl server setup
# Tested on Debian 13 "Trixie" (no GUI)
#
# Run as your normal user (not root). The script uses sudo where needed.
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
# =============================================================================

set -e  # stop immediately if any command fails

# ── Colors for output ─────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # no color

info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Config — edit these before running ────────────────────────────────────────
APP_USER=$(whoami)
APP_DIR="/home/$APP_USER/sq-codam"
DB_NAME="sq_codam"
DB_USER="sq_user"
DB_PASS="changeme_pick_a_strong_password"   # <-- change this
DOMAIN="sq.codam.nl"                         # <-- or your local IP for dev
APP_PORT="8080"

# =============================================================================
# STEP 1 — System update
# =============================================================================
info "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# =============================================================================
# STEP 2 — Install core packages
# =============================================================================
info "Installing core packages..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    curl \
    ufw \
    certbot \
    python3-certbot-nginx \
    build-essential \
    libpq-dev          # needed for psycopg2

info "Installed versions:"
python3 --version
psql --version
nginx -v

# =============================================================================
# STEP 3 — PostgreSQL setup
# =============================================================================
info "Setting up PostgreSQL..."

# Start and enable PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create DB user and database
sudo -u postgres psql <<EOF
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
    CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
  END IF;
END
\$\$;

SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec
EOF

info "PostgreSQL: database '$DB_NAME' and user '$DB_USER' ready."

# =============================================================================
# STEP 4 — Project directory and Python environment
# =============================================================================
info "Setting up project directory..."

mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install \
    nicegui \
    sqlalchemy \
    psycopg2-binary \
    pydantic-settings \
    httpx \
    apscheduler \
    python-dotenv \
    requests

info "Python virtual environment ready at $APP_DIR/.venv"

# =============================================================================
# STEP 5 — .env file (template)
# =============================================================================
info "Creating .env template..."

if [ ! -f "$APP_DIR/.env" ]; then
cat > "$APP_DIR/.env" <<EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost/$DB_NAME
FT_CLIENT_ID=your_42_client_id
FT_CLIENT_SECRET=your_42_client_secret
FT_REDIRECT_URI=https://$DOMAIN/auth/callback
FOOTBALL_API_KEY=your_football_data_key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
EOF
    warning ".env created — fill in your 42 OAuth credentials before starting the app."
else
    info ".env already exists, skipping."
fi

# =============================================================================
# STEP 6 — Nginx config
# =============================================================================
info "Configuring Nginx..."

sudo tee /etc/nginx/sites-available/sq-codam > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    # Forward all traffic to NiceGUI app
    location / {
        proxy_pass         http://127.0.0.1:$APP_PORT;
        proxy_http_version 1.1;

        # Required for NiceGUI websockets
        proxy_set_header Upgrade    \$http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host              \$host;
        proxy_set_header X-Real-IP         \$remote_addr;
        proxy_set_header X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_read_timeout 86400;   # keep websocket alive
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/sq-codam /etc/nginx/sites-enabled/sq-codam

# Remove default site if still enabled
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
sudo nginx -t && sudo systemctl reload nginx
sudo systemctl enable nginx

info "Nginx configured and running."

# =============================================================================
# STEP 7 — Firewall
# =============================================================================
info "Configuring firewall..."

sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'   # opens port 80 (HTTP) and 443 (HTTPS)
sudo ufw --force enable

info "Firewall: SSH + HTTP/HTTPS allowed."

# =============================================================================
# STEP 8 — systemd service (keeps app alive)
# =============================================================================
info "Creating systemd service..."

sudo tee /etc/systemd/system/sq-codam.service > /dev/null <<EOF
[Unit]
Description=sq.codam.nl NiceGUI app
After=network.target postgresql.service

[Service]
User=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/python main.py
Restart=always
RestartSec=5

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sq-codam

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable sq-codam

info "systemd service 'sq-codam' registered (not started yet — run 'sudo systemctl start sq-codam' when ready)."

# =============================================================================
# STEP 9 — SSL certificate (only if running on real domain, skip for local dev)
# =============================================================================
if [[ "$DOMAIN" != "localhost" && "$DOMAIN" != *.*.*.* ]]; then
    info "Attempting SSL certificate for $DOMAIN..."
    warning "This will only work if DNS is already pointing to this server."
    read -p "Get SSL cert now? (y/N): " GET_CERT
    if [[ "$GET_CERT" =~ ^[Yy]$ ]]; then
        sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m admin@codam.nl
        info "SSL certificate installed. Auto-renewal enabled."
    else
        info "Skipping SSL — run later with: sudo certbot --nginx -d $DOMAIN"
    fi
else
    info "Skipping SSL (local dev mode)."
fi

# =============================================================================
# Done
# =============================================================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit $APP_DIR/.env with your real credentials"
echo "  2. Copy your project code into $APP_DIR"
echo "  3. Run database migrations:"
echo "       cd $APP_DIR && source .venv/bin/activate"
echo "       python -c 'from core.database import init_db; init_db()'"
echo "  4. Start the app:"
echo "       sudo systemctl start sq-codam"
echo "  5. Check logs:"
echo "       sudo journalctl -u sq-codam -f"
echo ""
echo "  App will be available at: http://$DOMAIN"
echo ""