from locust import HttpUser, between, task


class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_posts(self):
        self.client.get("/posts", name="GET /posts")

    @task(2)
    def get_users(self):
        self.client.get("/users", name="GET /users")

    @task(1)
    def get_single_post(self):
        self.client.get("/posts/1", name="GET /posts/1")
