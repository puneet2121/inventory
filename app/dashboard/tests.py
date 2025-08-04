from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class RootRedirectTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_root_redirect_when_logged_in(self):
        """Test that root URL redirects to dashboard when user is logged in"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertEqual(response.url, '/dashboard/')

    def test_root_redirect_when_not_logged_in(self):
        """Test that root URL redirects to login when user is not logged in"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertEqual(response.url, '/authentication/login/')

    def test_dashboard_access_when_logged_in(self):
        """Test that dashboard is accessible when logged in"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_redirect_when_not_logged_in(self):
        """Test that dashboard redirects to login when not logged in"""
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)  # Should redirect to login
