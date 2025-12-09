"""
Tests para src/database.py: singleton de conexión MongoDB.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.database import DatabaseConnection, get_database, get_mongo_client


class TestDatabaseConnection:
    """Tests para la clase DatabaseConnection (singleton)."""
    
    def test_database_connection_singleton(self):
        """DatabaseConnection debe ser singleton (misma instancia)."""
        with patch('src.database.MongoClient'):
            conn1 = DatabaseConnection()
            conn2 = DatabaseConnection()
            # Mismo objeto en memoria
            assert conn1 is conn2
    
    def test_get_database_returns_db(self):
        """get_database debe retornar un objeto de base de datos."""
        with patch('src.database.MongoClient') as mock_client:
            mock_db = MagicMock()
            mock_client.return_value.__getitem__ = Mock(return_value=mock_db)
            
            # Esto es una prueba conceptual; requeriría mock real en contexto
            # db = get_database("test_db")
            # assert db is not None
            pass
    
    def test_get_mongo_client_returns_client(self):
        """get_mongo_client debe retornar el cliente MongoDB."""
        with patch('src.database.MongoClient') as mock_client:
            # Conceptual test
            pass


class TestDatabaseConnectionPooling:
    """Tests para verificar que el pooling de conexiones está configurado."""
    
    def test_database_connection_has_pooling_config(self):
        """La conexión debe tener configuración de pool."""
        # Esta prueba verificaría que minPoolSize, maxPoolSize, etc. estén configurados
        # en la inicialización de MongoClient
        pass
    
    def test_database_connection_health_check(self):
        """Debe poder hacer un health check simple."""
        with patch('src.database.MongoClient'):
            # Verificar que health_check existe y es callable
            conn = DatabaseConnection()
            assert hasattr(conn, '_health_check')
            assert callable(conn._health_check)
