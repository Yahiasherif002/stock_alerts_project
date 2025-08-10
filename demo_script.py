# demo_script.py - Complete workflow demonstration
import requests
import json
import time
from decimal import Decimal

class StockAlertDemo:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.access_token = None
        self.headers = {'Content-Type': 'application/json'}
        
    def print_response(self, title, response):
        """Pretty print API responses"""
        print(f"\n{'='*50}")
        print(f"🎯 {title}")
        print(f"{'='*50}")
        print(f"Status Code: {response.status_code}")
        if response.status_code < 400:
            print("✅ SUCCESS")
            if response.content:
                data = response.json()
                print(json.dumps(data, indent=2))
        else:
            print("❌ ERROR")
            print(response.text)
        print(f"{'='*50}")

    def register_user(self):
        """Step 1: Register a test user"""
        data = {
            "username": "yahia_demo",
            "email": "yahiasherif001@gmail.com",
            "password": "DemoPass123",
            "password_confirm": "DemoPass123",
            "first_name": "Demo",
            "last_name": "User"
        }
        
        response = requests.post(
            f"{self.base_url}/api/auth/register/",
            headers=self.headers,
            json=data
        )
        
        self.print_response("USER REGISTRATION", response)
        return response.status_code == 201

    def login_user(self):
        """Step 2: Login and get JWT token"""
        data = {
            "username": "yahia_demo",
            "password": "DemoPass123"
        }
        
        response = requests.post(
            f"{self.base_url}/api/auth/login/",
            headers=self.headers,
            json=data
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access']
            self.headers['Authorization'] = f'Bearer {self.access_token}'
        
        self.print_response("USER LOGIN", response)
        return response.status_code == 200

    def view_stocks(self):
        """Step 3: View available stocks"""
        response = requests.get(
            f"{self.base_url}/api/stocks/",
            headers=self.headers
        )
        
        self.print_response("VIEW AVAILABLE STOCKS", response)
        
        if response.status_code == 200:
            stocks = response.json()
            print(f"\n📊 Found {len(stocks)} stocks:")
            for stock in stocks:
                print(f"  {stock['symbol']}: ${stock['current_price']} - {stock['name']}")
        
        return response.status_code == 200
    
    def create_threshold_alert(self):
        """Step 4: Create a threshold alert"""
        data = {
            "stock": 1,  # AAPL
            "alert_type": "THRESHOLD",
            "condition": ">",
            "threshold_price": "180.00"
        }
        
        response = requests.post(
            f"{self.base_url}/api/alerts/",
            headers=self.headers,
            json=data
        )
        
        self.print_response("CREATE THRESHOLD ALERT (AAPL > $180)", response)
        return response.status_code == 201

    def create_duration_alert(self):
        """Step 5: Create a duration alert"""
        data = {
            "stock": 4,  # TSLA
            "alert_type": "DURATION", 
            "condition": "<",
            "threshold_price": "250.00",
            "duration_minutes": 5  # 5 minutes for demo
        }
        
        response = requests.post(
            f"{self.base_url}/api/alerts/",
            headers=self.headers,
            json=data
        )
        
        self.print_response("CREATE DURATION ALERT (TSLA < $250 for 5min)", response)
        return response.status_code == 201

    def view_user_alerts(self):
        """Step 6: View user's alerts"""
        response = requests.get(
            f"{self.base_url}/api/alerts/",
            headers=self.headers
        )
        
        self.print_response("VIEW USER'S ALERTS", response)
        return response.status_code == 200

    def manual_stock_price_update(self):
        """Step 7: Trigger manual stock price update"""
        response = requests.post(
            f"{self.base_url}/api/stocks/refresh_prices/",
            headers=self.headers
        )
        
        self.print_response("MANUAL STOCK PRICE UPDATE", response)
        return response.status_code == 200

    def manual_alert_processing(self):
        """Step 8: Trigger manual alert processing"""
        response = requests.post(
            f"{self.base_url}/api/alerts/test_process_alerts/",
            headers=self.headers
        )
        
        self.print_response("MANUAL ALERT PROCESSING", response)
        return response.status_code == 200

    def view_triggered_alerts(self):
        """Step 9: View triggered alerts"""
        response = requests.get(
            f"{self.base_url}/api/alerts/triggered_alerts/",
            headers=self.headers
        )
        
        self.print_response("VIEW TRIGGERED ALERTS", response)
        return response.status_code == 200

    def view_alert_summary(self):
        """Step 10: View alert summary"""
        print("⚠️ Alert summary endpoint not found. Skipping this step.")
        return True

    def run_complete_demo(self):
        """Run the complete demonstration"""
        print("🚀 Starting Stock Alert System Demo")
        print("=" * 60)
        
        # Step 1: Register user
        if not self.register_user():
            print("❌ Registration failed - user might already exist")
        
        # Step 2: Login
        if not self.login_user():
            print("❌ Login failed - stopping demo")
            return False
        
        # Step 3: View stocks
        self.view_stocks()
        
        # Step 4: Create alerts
        self.create_threshold_alert()
        self.create_duration_alert()
        
        # Step 5: View created alerts
        self.view_user_alerts()
        
        # Step 6: Update stock prices
        print("\n⏳ Updating stock prices...")
        self.manual_stock_price_update()
        
        # Step 7: Process alerts
        print("\n🔍 Processing alerts...")
        self.manual_alert_processing()
        
        # Step 8: Check triggered alerts
        self.view_triggered_alerts()
        
        # Step 9: View summary (skipped)
        # self.view_alert_summary()
        
        print("\n🎉 Demo completed successfully!")
        print("Check your email for any notifications that were sent.")
        
        return True


if __name__ == "__main__":
    # Instructions
    print("""
    📋 DEMO SETUP INSTRUCTIONS:
    
    1. Make sure your Django server is running:
       python manage.py runserver
    
    2. Make sure you have populated stocks:
       python manage.py populate_stocks
    
    3. Make sure Celery is running (optional, for auto-processing):
       celery -A stock_alerts worker --loglevel=info
    
    4. Run this demo script:
       python demo_script.py
    
    This will demonstrate the complete user workflow!
    """)
    
    input("Press Enter to continue...")
    
    # Run the demo
    demo = StockAlertDemo()
    demo.run_complete_demo()


# Additional utility functions for testing specific scenarios

def test_error_scenarios():
    """Test error handling"""
    demo = StockAlertDemo()
    
    # Test invalid registration
    print("Testing invalid registration (password mismatch)...")
    response = requests.post(
        f"{demo.base_url}/api/auth/register/",
        headers=demo.headers,
        json={
            "username": "testuser",
            "email": "test@example.com", 
            "password": "pass123",
            "password_confirm": "different_pass"
        }
    )
    demo.print_response("INVALID REGISTRATION", response)
    
    # Test invalid alert creation
    print("Testing invalid alert (missing duration)...")
    # First login
    demo.login_user()
    
    response = requests.post(
        f"{demo.base_url}/api/alerts/",
        headers=demo.headers,
        json={
            "stock": 1,
            "alert_type": "DURATION",
            "condition": ">",
            "threshold_price": "180.00"
            # Missing duration_minutes!
        }
    )
    demo.print_response("INVALID ALERT CREATION", response)

def simulate_alert_trigger():
    """Simulate an alert being triggered by manually setting stock price"""
    print("""
    🎯 ALERT TRIGGER SIMULATION:
    
    To see an alert actually trigger:
    
    1. Create an alert with threshold close to current price
    2. Go to Django admin: http://localhost:8000/admin/
    3. Navigate to Stocks -> Stocks
    4. Manually change a stock price to cross your threshold
    5. Run: python manage.py process_alerts
    6. Check console output and your email!
    """)

if __name__ == "__main__":
    print("Choose demo mode:")
    print("1. Complete workflow demo")
    print("2. Error scenario testing") 
    print("3. Alert trigger simulation guide")
    
    choice = input("Enter choice (1-3): ")
    
    if choice == "1":
        demo = StockAlertDemo()
        demo.run_complete_demo()
    elif choice == "2":
        test_error_scenarios()
    elif choice == "3":
        simulate_alert_trigger()
    else:
        print("Invalid choice")
