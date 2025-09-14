#!/usr/bin/env python3
"""Test script to verify Flask app functionality"""

from app import create_app

def test_app():
    """Test basic Flask app functionality"""
    print("Creating Flask app...")
    app = create_app()

    print("Testing app routes with test client...")
    with app.test_client() as client:
        # Test index route
        response = client.get('/')
        print(f"Index route status: {response.status_code}")

        # Test auth routes
        response = client.get('/auth/login')
        print(f"Login route status: {response.status_code}")

        response = client.get('/auth/signup')
        print(f"Signup route status: {response.status_code}")

        # Test admin routes (should redirect to login)
        response = client.get('/admin/dashboard')
        print(f"Admin dashboard route status: {response.status_code}")

    print("App testing completed successfully!")

if __name__ == '__main__':
    test_app()
