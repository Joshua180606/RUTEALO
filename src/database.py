"""
Database connection and pooling management.

Centralizes MongoDB connection handling with:
- Connection pooling configuration
- Retry logic and health checks
- Singleton pattern to prevent connection leaks
- Graceful shutdown
"""

import os
from typing import Optional
from pymongo import MongoClient, errors
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Singleton class for MongoDB connection management with pooling."""

    _instance: Optional["DatabaseConnection"] = None
    _client: Optional[MongoClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize database connection only once."""
        if self._client is None:
            self._connect()

    def _connect(self) -> None:
        """
        Establish MongoDB connection with pooling and retry logic.

        Uses configuration from src.config:
        - MONGO_URI: Connection string
        - MONGODB_POOL_SIZE: Max connections in pool
        - MONGODB_CONNECT_TIMEOUT: Connection timeout in ms
        - MONGODB_SOCKET_TIMEOUT: Socket timeout in ms
        """
        try:
            from src.config import (
                MONGO_URI,
                MONGODB_POOL_SIZE,
                MONGODB_CONNECT_TIMEOUT,
                MONGODB_SOCKET_TIMEOUT,
                MONGODB_MAX_POOL_SIZE,
                MONGODB_MIN_POOL_SIZE,
            )

            logger.info("Iniciando conexión a MongoDB...")

            # Create client with pooling configuration
            self._client = MongoClient(
                MONGO_URI,
                maxPoolSize=MONGODB_MAX_POOL_SIZE,
                minPoolSize=MONGODB_MIN_POOL_SIZE,
                maxIdleTimeMS=MONGODB_POOL_SIZE,
                connectTimeoutMS=MONGODB_CONNECT_TIMEOUT,
                socketTimeoutMS=MONGODB_SOCKET_TIMEOUT,
                serverSelectionTimeoutMS=MONGODB_CONNECT_TIMEOUT,
                retryWrites=True,
                retryReads=True,
                w="majority",  # Wait for majority of replicas to acknowledge
            )

            # Verify connection with health check
            self._health_check()
            logger.info("Conexion a MongoDB establecida correctamente")

        except Exception as e:
            logger.error(f"Error al conectar a MongoDB: {str(e)}")
            self._client = None
            raise

    def _health_check(self) -> None:
        """
        Verify MongoDB connection is working.

        Raises:
            ConnectionFailure: If server is not accessible
        """
        try:
            if self._client is None:
                raise ConnectionFailure("MongoClient not initialized")

            # Perform server selection to verify connection
            self._client.admin.command("ping")
            logger.debug("Health check passed")

        except (ServerSelectionTimeoutError, ConnectionFailure) as e:
            logger.error(f"Health check failed: {str(e)}")
            self._client = None
            raise

    def get_client(self) -> MongoClient:
        """
        Get MongoDB client instance.

        Returns:
            MongoClient: Connected MongoDB client

        Raises:
            RuntimeError: If connection failed
        """
        if self._client is None:
            raise RuntimeError("Database connection not initialized")
        return self._client

    def get_database(self, db_name: str):
        """
        Get database instance from connected client.

        Args:
            db_name: Database name

        Returns:
            Database instance
        """
        if self._client is None:
            raise RuntimeError("Database connection not initialized")
        return self._client[db_name]

    def close(self) -> None:
        """Close database connection and cleanup resources."""
        try:
            if self._client is not None:
                self._client.close()
                logger.info("MongoDB connection closed")
                self._client = None
        except Exception as e:
            logger.error(f"Error closing connection: {str(e)}")

    def reconnect(self) -> None:
        """Reconnect to database (useful for connection recovery)."""
        self.close()
        self._connect()

    def is_connected(self) -> bool:
        """Check if database is currently connected."""
        try:
            if self._client is None:
                return False
            self._health_check()
            return True
        except Exception:
            return False


def get_database_connection() -> DatabaseConnection:
    """
    Get or create database connection singleton.

    Returns:
        DatabaseConnection: Singleton instance
    """
    return DatabaseConnection()


def get_database(db_name: Optional[str] = None):
    """
    Convenience function to get database instance.

    Args:
        db_name: Database name (defaults to DB_NAME from config)

    Returns:
        Database instance
    """
    if db_name is None:
        from src.config import DB_NAME

        db_name = DB_NAME

    return get_database_connection().get_database(db_name)


def get_mongo_client() -> MongoClient:
    """
    Convenience function to get MongoDB client.

    Returns:
        MongoClient: Connected client
    """
    return get_database_connection().get_client()
