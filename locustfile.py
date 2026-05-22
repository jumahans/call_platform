"""
Load test for the call platform.
Run with: locust -f locustfile.py --host=http://localhost:8000
Then open http://localhost:8089 in your browser.
"""

from locust import HttpUser, task, between
import random
import string


def random_email():
    return f"load_{''.join(random.choices(string.ascii_lowercase, k=10))}@test.com"


class CallPlatformUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        """Register and login a fresh user when each simulated user starts."""
        email = random_email()
        password = "LoadTest123"

        self.client.post("/api/accounts/register", json={
            "email": email,
            "password": password,
            "first_name": "Load",
            "last_name": "Test",
            "organization_name": f"LoadOrg_{random.randint(1000, 9999)}",
        })

        response = self.client.post("/api/accounts/login", json={
            "email": email,
            "password": password,
        })

        if response.status_code == 200:
            self.token = response.json().get("access")

    @property
    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(3)
    def get_dashboard(self):
        self.client.get("/api/analytics/dashboard", headers=self.auth_headers)

    @task(3)
    def list_campaigns(self):
        self.client.get("/api/campaigns/", headers=self.auth_headers)

    @task(2)
    def list_buyers(self):
        self.client.get("/api/buyers/", headers=self.auth_headers)

    @task(2)
    def list_calls(self):
        self.client.get("/api/routing/calls", headers=self.auth_headers)

    @task(1)
    def create_campaign(self):
        self.client.post("/api/campaigns/", headers=self.auth_headers, json={
            "name": f"LoadTest Campaign {random.randint(1, 100000)}",
            "routing_type": "priority",
            "payout_amount": 5.00,
            "revenue_amount": 12.50,
            "bid_floor": 2.00,
            "rtb_timeout_seconds": 5,
        })

    @task(1)
    def create_buyer(self):
        self.client.post("/api/buyers/", headers=self.auth_headers, json={
            "name": f"LoadTest Buyer {random.randint(1, 100000)}",
            "max_concurrency": 5,
            "dup_window_days": 30,
            "quality_score": 50,
        })

    @task(2)
    def caller_profile(self):
        random_number = f"+1555{random.randint(1000000, 9999999)}"
        self.client.get(f"/api/analytics/caller-profile/{random_number}", headers=self.auth_headers)