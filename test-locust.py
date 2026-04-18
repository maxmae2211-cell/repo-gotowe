"""
Test Locust z Taurus
Locust to framework do testów obciążeniowych napisany w Pythonie
"""
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 5)  # Czekaj 1-5 sekund między requestami
    
    @task(3)  # 3x bardziej popularne
    def get_users(self):
        """Pobierz listę użytkowników"""
        self.client.get("/users", name="/users")
    
    @task(1)  # 1x mniej popularne
    def get_posts(self):
        """Pobierz listę postów"""
        self.client.get("/posts", name="/posts")
    
    @task(2)  # 2x bardziej popularne
    def get_comments(self):
        """Pobierz listę komentarzy"""
        self.client.get("/comments", name="/comments")
    
    def on_start(self):
        """Kod wykonany na starcie user'a"""
        print("User started")
    
    def on_stop(self):
        """Kod wykonany na zakończeniu user'a"""
        print("User stopped")
