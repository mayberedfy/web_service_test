import unittest
from src.app import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to the Flask Web Service', response.data)

    def test_not_found(self):
        response = self.app.get('/nonexistent')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()