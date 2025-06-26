#!/usr/bin/env python3
"""
Production Setup Script
This script sets up the application for production deployment without breaking existing functionality.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionSetup:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.env_file = self.base_dir / '.env'
        
    def check_prerequisites(self):
        """Check if all prerequisites are installed"""
        logger.info("Checking prerequisites...")
        
        required_tools = ['docker', 'docker-compose', 'python3', 'pip']
        missing_tools = []
        
        for tool in required_tools:
            try:
                subprocess.run([tool, '--version'], capture_output=True, check=True)
                logger.info(f"✅ {tool} is installed")
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(tool)
                logger.error(f"❌ {tool} is not installed")
        
        if missing_tools:
            logger.error(f"Missing tools: {', '.join(missing_tools)}")
            logger.error("Please install the missing tools before proceeding.")
            return False
        
        return True
    
    def create_env_file(self):
        """Create .env file with production configuration"""
        logger.info("Creating .env file...")
        
        env_content = """# Production Environment Configuration

# Database Configuration
DATABASE_URL=postgresql://desidelight_user:desidelight_password@localhost:5432/desidelight
REDIS_URL=redis://localhost:6379

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secret-production-key-change-this
DEBUG=False

# Security Configuration
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
CORS_ORIGINS=["https://yourdomain.com"]

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Rate Limiting
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=900

# File Upload Configuration
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=upload
ALLOWED_EXTENSIONS=csv,xlsx,xls

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-password

# AI Configuration
AI_MODEL_PATH=models/
AI_CACHE_ENABLED=True
"""
        
        try:
            with open(self.env_file, 'w') as f:
                f.write(env_content)
            logger.info("✅ .env file created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create .env file: {e}")
            return False
    
    def create_directories(self):
        """Create necessary directories"""
        logger.info("Creating necessary directories...")
        
        directories = [
            'logs',
            'models',
            'upload',
            'backups',
            'ssl'
        ]
        
        for directory in directories:
            dir_path = self.base_dir / directory
            try:
                dir_path.mkdir(exist_ok=True)
                logger.info(f"✅ Created directory: {directory}")
            except Exception as e:
                logger.error(f"❌ Failed to create directory {directory}: {e}")
                return False
        
        return True
    
    def setup_ssl_certificates(self):
        """Setup SSL certificates for HTTPS"""
        logger.info("Setting up SSL certificates...")
        
        ssl_dir = self.base_dir / 'ssl'
        
        # Create self-signed certificate for development
        try:
            subprocess.run([
                'openssl', 'req', '-x509', '-newkey', 'rsa:4096', '-keyout', 
                str(ssl_dir / 'key.pem'), '-out', str(ssl_dir / 'cert.pem'), 
                '-days', '365', '-nodes', '-subj', '/CN=localhost'
            ], check=True, capture_output=True)
            
            logger.info("✅ SSL certificates created successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️  Failed to create SSL certificates: {e}")
            logger.warning("You can create them manually or use a reverse proxy")
            return True  # Don't fail the setup for this
    
    def install_dependencies(self):
        """Install Python dependencies"""
        logger.info("Installing Python dependencies...")
        
        try:
            subprocess.run([
                'pip', 'install', '-r', 'requirements.txt'
            ], check=True)
            logger.info("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
    
    def setup_database(self):
        """Setup PostgreSQL database"""
        logger.info("Setting up PostgreSQL database...")
        
        try:
            # Start PostgreSQL using Docker Compose
            subprocess.run([
                'docker-compose', 'up', '-d', 'postgres', 'redis'
            ], check=True)
            
            logger.info("✅ PostgreSQL and Redis started successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to start database: {e}")
            return False
    
    def run_migrations(self):
        """Run database migrations"""
        logger.info("Running database migrations...")
        
        try:
            # Wait for database to be ready
            import time
            time.sleep(5)
            
            # Run migrations
            subprocess.run([
                'python', 'src/create_db.py'
            ], check=True)
            
            logger.info("✅ Database migrations completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to run migrations: {e}")
            return False
    
    def create_systemd_service(self):
        """Create systemd service file for production"""
        logger.info("Creating systemd service file...")
        
        service_content = f"""[Unit]
Description=DesiDelight Analytics API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory={self.base_dir}
Environment=PATH={self.base_dir}/venv/bin
ExecStart={self.base_dir}/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 src.main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path('/etc/systemd/system/desidelight-api.service')
        
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            # Reload systemd and enable service
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'enable', 'desidelight-api'], check=True)
            
            logger.info("✅ Systemd service created and enabled")
            return True
        except Exception as e:
            logger.warning(f"⚠️  Failed to create systemd service: {e}")
            logger.warning("You can create it manually or use a different process manager")
            return True  # Don't fail the setup for this
    
    def create_nginx_config(self):
        """Create Nginx configuration"""
        logger.info("Creating Nginx configuration...")
        
        nginx_config = """server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/your/ssl/cert.pem;
    ssl_certificate_key /path/to/your/ssl/key.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/frontend/dist/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
"""
        
        nginx_file = self.base_dir / 'nginx.conf'
        
        try:
            with open(nginx_file, 'w') as f:
                f.write(nginx_config)
            
            logger.info("✅ Nginx configuration created")
            logger.info(f"📁 Configuration saved to: {nginx_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create Nginx config: {e}")
            return False
    
    def create_backup_script(self):
        """Create automated backup script"""
        logger.info("Creating backup script...")
        
        backup_script = """#!/bin/bash
# Automated backup script for DesiDelight Analytics

BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="desidelight"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup PostgreSQL database
pg_dump -h localhost -U desidelight_user $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Backup uploaded files
tar -czf $BACKUP_DIR/uploads_backup_$DATE.tar.gz upload/

# Backup AI models
tar -czf $BACKUP_DIR/models_backup_$DATE.tar.gz models/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
"""
        
        backup_file = self.base_dir / 'backup.sh'
        
        try:
            with open(backup_file, 'w') as f:
                f.write(backup_script)
            
            # Make executable
            os.chmod(backup_file, 0o755)
            
            logger.info("✅ Backup script created")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create backup script: {e}")
            return False
    
    def run_setup(self):
        """Run the complete production setup"""
        logger.info("🚀 Starting production setup...")
        
        steps = [
            ("Checking prerequisites", self.check_prerequisites),
            ("Creating directories", self.create_directories),
            ("Creating .env file", self.create_env_file),
            ("Setting up SSL certificates", self.setup_ssl_certificates),
            ("Installing dependencies", self.install_dependencies),
            ("Setting up database", self.setup_database),
            ("Running migrations", self.run_migrations),
            ("Creating systemd service", self.create_systemd_service),
            ("Creating Nginx config", self.create_nginx_config),
            ("Creating backup script", self.create_backup_script)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n📋 {step_name}...")
            if not step_func():
                logger.error(f"❌ Setup failed at: {step_name}")
                return False
        
        logger.info("\n🎉 Production setup completed successfully!")
        logger.info("\n📝 Next steps:")
        logger.info("1. Update the .env file with your production values")
        logger.info("2. Configure your domain in the Nginx config")
        logger.info("3. Set up SSL certificates for your domain")
        logger.info("4. Start the application: systemctl start desidelight-api")
        logger.info("5. Set up automated backups using the backup script")
        
        return True

def main():
    """Main setup function"""
    setup = ProductionSetup()
    
    if not setup.run_setup():
        logger.error("❌ Production setup failed!")
        sys.exit(1)
    
    logger.info("✅ Production setup completed successfully!")

if __name__ == "__main__":
    main() 