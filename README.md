# 📈 Stock Price Alerting System

A comprehensive Django-based stock price monitoring and alerting system that allows users to set up custom alerts and receive notifications when specific price conditions are met.

## 🎯 Features

- **Real-time Stock Tracking**: Monitors 10 predefined stocks using free APIs  
- **Flexible Alert Types**:  
  - Threshold Alerts: Trigger when price crosses a threshold  
  - Duration Alerts: Trigger when price stays in condition for X minutes  
- **Multiple Notification Methods**: Email notifications with console fallback  
- **RESTful API**: Complete JWT-based API for frontend integration  
- **Background Processing**: Automated price fetching and alert checking  
- **AWS Deployment**: Ready for production deployment on AWS Free Tier  

## 🛠️ Tech Stack

- **Backend:** Django 4.2, Django REST Framework  
- **Authentication:** JWT (Simple JWT)  
- **Database:** SQLite (dev) / PostgreSQL (production)  
- **Background Tasks:** Celery with Redis  
- **Stock Data:** Twelve Data API (primary) & Alpha Vantage API (backup) with automatic failover    
- **Notifications:** Email (SMTP) / Console logging
- **Testing:** Pytest
- **Deployment:** AWS EC2, Nginx, Gunicorn  

## 📊 Monitored Stocks

- AAPL (Apple Inc.)  
- GOOGL (Alphabet Inc.)  
- MSFT (Microsoft Corporation)  
- TSLA (Tesla Inc.)  
- AMZN (Amazon.com Inc.)  
- META (Meta Platforms Inc.)  
- NVDA (NVIDIA Corporation)  
- NFLX (Netflix Inc.)  
- AMD (Advanced Micro Devices Inc.)  
- UBER (Uber Technologies Inc.)  

## 🚀 Quick Start

### Prerequisites
- Python 3.8+  
- Redis (for background tasks)  
- Free API key from Twelve Data  

### Installation

```bash
# Clone the repository
git clone https://github.com/Yahiasherif002/stock_alerts_project/
cd stock_alerts_project

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# Set up database
python manage.py migrate
python manage.py createsuperuser
python manage.py populate_stocks

# Start the development server
python manage.py runserver
```

### Start background tasks (in separate terminals)

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery Worker
celery -A stock_alerts worker --loglevel=info

# Terminal 3: Celery Beat (Scheduler)
celery -A stock_alerts beat --loglevel=info
```

## 📧 Email Configuration

### Gmail Setup (Development)

1. Enable 2-factor authentication on your Gmail account  
2. Generate an "App Password" for this application  
3. Add to your `.env`:
```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
```

## 🔑 API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration  
- `POST /api/auth/login/` - Login (get JWT tokens)  
- `POST /api/auth/refresh/` - Refresh access token  
- `GET /api/auth/profile/` - Get user profile
- `POST /api/auth/custom-login/` - custom token obtain pair

### Stocks
- `GET /api/stocks/` - List all tracked stocks  
- `GET /api/stocks/<symbol>/` - Get specific stock data  
- `POST /api/stocks/actions/refresh-prices/` - Manually refresh prices  

### Alerts
- `GET /api/alerts/` - List user's alerts  
- `POST /api/alerts/` - Create new alert  
- `GET /api/alerts/<id>/` - Get specific alert  
- `PUT /api/alerts/<id>/` - Update alert  
- `DELETE /api/alerts/<id>/` - Delete alert  
- `GET /api/alerts/triggered/` - List triggered alerts  
- `GET /api/alerts/summary/` - Get alerts summary  

## 📝 API Usage Examples

### Register and Login
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register/   -H "Content-Type: application/json"   -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "strongpassword123",
    "password_confirm": "strongpassword123"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login/   -H "Content-Type: application/json"   -d '{
    "username": "testuser",
    "password": "strongpassword123"
  }'
```

### Create Alerts
```bash
# Threshold Alert: AAPL > $200
curl -X POST http://localhost:8000/api/alerts/   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"   -H "Content-Type: application/json"   -d '{
    "stock": 1,
    "alert_type": "THRESHOLD", 
    "condition": ">",
    "threshold_price": "200.00"
  }'

# Duration Alert: TSLA < $150 for 30 minutes
curl -X POST http://localhost:8000/api/alerts/   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"   -H "Content-Type: application/json"   -d '{
    "stock": 4,
    "alert_type": "DURATION",
    "condition": "<", 
    "threshold_price": "150.00",
    "duration_minutes": 30
  }'
```

## 🧪 Testing

### Manual Testing Commands
```bash
# Test stock price fetching
python manage.py fetch_prices --all

# Test alert processing  
python manage.py process_alerts

# Test email configuration
python manage.py test_email your-email@example.com

# Create sample alerts for testing
python manage.py create_sample_alerts your-username
```

### Automated Testing
```bash
python manage.py test
```

## 🔄 Background Tasks

The system uses Celery for automated background processing:

- Stock Price Updates: Every 3 minutes  
- Alert Processing: Every 2 minutes  
- Cleanup Old Records: Daily at midnight  

### Task Schedule
```python
CELERY_BEAT_SCHEDULE = {
    'fetch-stock-prices': {
        'task': 'apps.stocks.tasks.fetch_all_stock_prices',
        'schedule': 300.0,  # 5 minutes
    },
    'process-alerts': {
        'task': 'apps.alerts.tasks.process_all_alerts', 
        'schedule': 120.0,  # 2 minutes
    }
}


```

## 🌐 AWS Deployment

The system is designed for easy deployment on AWS Free Tier:

**Architecture**
- EC2 t2.micro: Django app with Nginx/Gunicorn  
- RDS PostgreSQL (optional): Production database  
- Redis on EC2: Background task queue  
- SES: Email notifications (production)  

**Deployment Steps**
1. Launch EC2 instance (Ubuntu 22.04 LTS)  
2. Install dependencies and clone project  
3. Configure Nginx as reverse proxy  
4. Set up Systemd services for Django, Celery  
5. Configure domain and SSL (optional)  

See AWS Deployment Guide for detailed instructions.

## 📊 Sample Data

**Test Stocks** (populated by default)  
The system comes with 10 predefined stocks that are automatically tracked.

**Sample Alert Scenarios**
- Bull Market Alert: AAPL > $180 (threshold)  
- Bear Market Protection: TSLA < $200 for 1 hour (duration)  
- Buying Opportunity: GOOGL <= $160 (threshold)  

## 🔍 Monitoring

**Health Check Endpoints**
- `GET /api/stocks/` - Verify API is responding  
- `GET /admin/` - Django admin interface  

**Log Files**
- Django: `logs/django.log`  
- Celery: Check systemd journal logs  

**System Commands**
```bash
# Check service status
systemctl status stock_alerts celery celerybeat

# View recent logs
journalctl -u stock_alerts --since "1 hour ago"

# Monitor background tasks
celery -A stock_alerts inspect active
```

## 🤝 Contributing

1. Fork the repository  
2. Create a feature branch (`git checkout -b feature/amazing-feature`)  
3. Commit your changes (`git commit -m 'Add amazing feature'`)  
4. Push to the branch (`git push origin feature/amazing-feature`)  
5. Open a Pull Request  

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues

**Stock prices not updating?**
- Check your API key in `.env`  
- Verify internet connection  
- Check API rate limits (800/day for free tier)  

**Alerts not triggering?**
- Verify alert conditions in admin panel  
- Check that stock prices are current  
- Run `python manage.py process_alerts` manually  

**Email notifications not working?**
- Use Gmail App Password, not regular password  
- Check `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in `.env`  
- Test with `python manage.py test_email your-email@example.com`  

### Get Help
- Check the Issues page  
- Review the Documentation  
- Contact: yahyasheriif@gmail.com  

---
Built with ❤️from YAHYA using Django and deployed on AWS Free Tier
