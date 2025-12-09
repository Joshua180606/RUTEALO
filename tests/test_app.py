"""
Tests para src/app.py: rutas Flask y manejo de errores.
"""

import pytest
from src.app import app, db


@pytest.fixture
def client():
    """Cliente Flask para pruebas."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestAppRoutes:
    """Tests para las rutas principales de la aplicación."""
    
    def test_index_route_returns_200(self, client):
        """GET / debe retornar 200."""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_index_route_returns_html(self, client):
        """GET / debe retornar HTML."""
        response = client.get('/')
        assert response.content_type.startswith('text/html')
    
    def test_login_route_get_returns_200(self, client):
        """GET /login debe retornar 200."""
        response = client.get('/login')
        assert response.status_code == 200
    
    def test_register_route_get_returns_200(self, client):
        """GET /register debe retornar 200."""
        response = client.get('/register')
        assert response.status_code == 200


class TestErrorHandling:
    """Tests para el manejo de errores en la app."""
    
    def test_404_error_page(self, client):
        """Acceder a ruta inexistente debe retornar 404."""
        response = client.get('/nonexistent-route')
        assert response.status_code == 404
    
    def test_app_initializes_successfully(self):
        """La app debe inicializarse sin errores."""
        assert app is not None
        assert app.config.get('SECRET_KEY') is not None
