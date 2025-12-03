# Production Deployment Guide

This guide covers deploying the Stroke Prediction System to a production environment.

## Pre-Deployment Checklist

- [ ] All security features tested
- [ ] MongoDB configured with authentication
- [ ] HTTPS/SSL certificates obtained
- [ ] Production server prepared
- [ ] Backup strategy defined
- [ ] Monitoring tools selected
- [ ] Domain name configured (if applicable)

## Production Configuration

### 1. Environment Variables

Create a production `.env` file:

```bash
# Production .env file
SECRET_KEY=<generate-strong-random-key-here>
MONGO_URI=mongodb://username:password@localhost:27017/stroke_prediction?authSource=admin
SESSION_COOKIE_SECURE=True
FLASK_ENV=production
```

**Generate Strong Secret Key**:
```python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2. MongoDB Production Setup

```bash
# Start MongoDB with authentication
sudo systemctl start mongod

# Connect to MongoDB
mongosh

# Switch to admin database
use admin

# Create admin user
db.createUser({
  user: "admin",
  pwd: passwordPrompt(),  # Will prompt for password
  roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
})

# Create application user
use stroke_prediction
db.createUser({
  user: "stroke_app",
  pwd: passwordPrompt(),
  roles: [ { role: "readWrite", db: "stroke_prediction" } ]
})

# Exit
exit
```

Edit MongoDB config to enable authentication:
```bash
sudo nano /etc/mongod.conf
```

Add:
```yaml
security:
  authorization: enabled
```

Restart MongoDB:
```bash
sudo systemctl restart mongod
```

### 3. Application Configuration

Update [app.py](app.py) for production:

```python
# Line 583 - Change debug mode
if __name__ == '__main__':
    init_user_db()
    logger.info("Application started")
    app.run(debug=False, host='0.0.0.0', port=5000)  # debug=False for production
```

## Deployment Options

### Option 1: Deploy with Gunicorn (Recommended)

#### Install Gunicorn
```bash
pip install gunicorn
```

Add to requirements.txt:
```
gunicorn==21.2.0
```

#### Create Gunicorn Configuration

Create `gunicorn_config.py`:
```python
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/log/stroke_app/access.log"
errorlog = "/var/log/stroke_app/error.log"
loglevel = "info"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
```

#### Create Log Directory
```bash
sudo mkdir -p /var/log/stroke_app
sudo chown $USER:$USER /var/log/stroke_app
```

#### Run with Gunicorn
```bash
gunicorn -c gunicorn_config.py app:app
```

### Option 2: Deploy with uWSGI

#### Install uWSGI
```bash
pip install uwsgi
```

#### Create uWSGI Configuration

Create `uwsgi.ini`:
```ini
[uwsgi]
module = app:app
master = true
processes = 4
threads = 2
socket = 0.0.0.0:5000
protocol = http
chmod-socket = 660
vacuum = true
die-on-term = true
```

#### Run with uWSGI
```bash
uwsgi --ini uwsgi.ini
```

## Systemd Service Setup

Create systemd service for automatic startup:

### Create Service File
```bash
sudo nano /etc/systemd/system/stroke-app.service
```

### Service Configuration
```ini
[Unit]
Description=Stroke Prediction System
After=network.target mongodb.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/stroke-app
Environment="PATH=/var/www/stroke-app/venv/bin"
ExecStart=/var/www/stroke-app/venv/bin/gunicorn -c gunicorn_config.py app:app

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable stroke-app
sudo systemctl start stroke-app
sudo systemctl status stroke-app
```

## Nginx Reverse Proxy Setup

### Install Nginx
```bash
sudo apt update
sudo apt install nginx
```

### Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/stroke-app
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static {
        alias /var/www/stroke-app/static;
        expires 30d;
    }

    # Logging
    access_log /var/log/nginx/stroke-app-access.log;
    error_log /var/log/nginx/stroke-app-error.log;
}
```

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/stroke-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## SSL/TLS Certificate (Let's Encrypt)

### Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

### Obtain Certificate
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### Auto-Renewal
Certbot automatically sets up renewal. Test it:
```bash
sudo certbot renew --dry-run
```

## Firewall Configuration

### UFW (Ubuntu)
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
sudo ufw status
```

### Firewalld (CentOS/RHEL)
```bash
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## Security Hardening

### 1. Update Application for Production

Edit [app.py](app.py):

```python
# Line 30 - Enable secure cookies
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only

# Add security headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

### 2. Rate Limiting

Install Flask-Limiter:
```bash
pip install Flask-Limiter
```

Add to app.py:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    # ... existing code
```

### 3. Database Backups

Create backup script `backup.sh`:
```bash
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/stroke-app"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup MongoDB
mongodump --uri="mongodb://username:password@localhost:27017/stroke_prediction" \
  --out="$BACKUP_DIR/mongodb_$TIMESTAMP"

# Backup SQLite
cp /var/www/stroke-app/users.db "$BACKUP_DIR/users_$TIMESTAMP.db"

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete
find $BACKUP_DIR -type d -mtime +7 -delete

echo "Backup completed: $TIMESTAMP"
```

Make executable:
```bash
chmod +x backup.sh
```

Add to crontab (daily at 2 AM):
```bash
crontab -e
# Add:
0 2 * * * /var/www/stroke-app/backup.sh >> /var/log/stroke-app/backup.log 2>&1
```

### 4. Log Rotation

Create `/etc/logrotate.d/stroke-app`:
```
/var/log/stroke_app/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload stroke-app > /dev/null 2>&1 || true
    endscript
}
```

## Monitoring Setup

### 1. Application Monitoring

Install monitoring tools:
```bash
pip install flask-healthz
```

Add health check endpoint to app.py:
```python
from flask_healthz import healthz

app.register_blueprint(healthz, url_prefix="/healthz")

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
```

### 2. System Monitoring

Install monitoring tools:
```bash
sudo apt install prometheus-node-exporter
```

### 3. Uptime Monitoring

Use external services:
- UptimeRobot (https://uptimerobot.com)
- Pingdom (https://www.pingdom.com)
- StatusCake (https://www.statuscake.com)

## Deployment Checklist

### Pre-Deployment
- [ ] Code tested thoroughly
- [ ] Security audit completed
- [ ] Dependencies updated
- [ ] Documentation reviewed
- [ ] Backup strategy implemented

### Server Setup
- [ ] Server provisioned
- [ ] SSH access configured
- [ ] Firewall configured
- [ ] Nginx installed
- [ ] MongoDB installed and secured

### Application Setup
- [ ] Code deployed to server
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Environment variables configured
- [ ] Database initialized
- [ ] Data imported

### Security
- [ ] HTTPS enabled
- [ ] SSL certificate installed
- [ ] Secure cookies enabled
- [ ] MongoDB authentication enabled
- [ ] Strong SECRET_KEY set
- [ ] Rate limiting implemented
- [ ] Security headers added

### Monitoring
- [ ] Logs configured
- [ ] Log rotation set up
- [ ] Backups automated
- [ ] Health checks working
- [ ] Monitoring tools configured
- [ ] Uptime monitoring active

### Post-Deployment
- [ ] Test all functionality
- [ ] Verify HTTPS working
- [ ] Check logs
- [ ] Test backups
- [ ] Verify monitoring alerts
- [ ] Document deployment

## Troubleshooting

### Application Won't Start
```bash
# Check logs
sudo journalctl -u stroke-app -n 50

# Check Gunicorn
sudo systemctl status stroke-app

# Check Nginx
sudo nginx -t
sudo systemctl status nginx
```

### Database Connection Issues
```bash
# Check MongoDB
sudo systemctl status mongod

# Test connection
mongosh -u username -p password --authenticationDatabase admin
```

### Performance Issues
```bash
# Check system resources
htop
df -h
free -h

# Check application logs
tail -f /var/log/stroke_app/error.log
```

## Maintenance

### Regular Tasks
- Weekly: Review logs for errors
- Weekly: Check disk space
- Monthly: Review security updates
- Monthly: Test backup restoration
- Quarterly: Security audit
- Quarterly: Dependency updates

### Update Procedure
```bash
# Backup first
./backup.sh

# Pull latest code
cd /var/www/stroke-app
git pull

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart application
sudo systemctl restart stroke-app
```

## Support & Resources

- Flask Documentation: https://flask.palletsprojects.com/
- MongoDB Documentation: https://docs.mongodb.com/
- Nginx Documentation: https://nginx.org/en/docs/
- Let's Encrypt: https://letsencrypt.org/
- OWASP: https://owasp.org/

---

**Production Deployment Status**: [ ] Not Started / [ ] In Progress / [ ] Complete
