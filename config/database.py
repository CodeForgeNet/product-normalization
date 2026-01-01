"""
Database Configuration and Connection Manager
"""
import psycopg
from psycopg.rows import dict_row
from psycopg import sql
from contextlib import contextmanager
import os
from typing import Optional, List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration"""
    HOST = os.getenv('DB_HOST', 'localhost')
    PORT = os.getenv('DB_PORT', '5432')
    DATABASE = os.getenv('DB_NAME', 'product_normalization')
    USER = os.getenv('DB_USER', 'hackathon')
    PASSWORD = os.getenv('DB_PASSWORD', 'hackathon123')
    
    @classmethod
    def get_connection_string(cls) -> str:
        return f"host={cls.HOST} port={cls.PORT} dbname={cls.DATABASE} user={cls.USER} password={cls.PASSWORD}"


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self._connection = None
    
    def connect(self) -> psycopg.Connection:
        """Establish database connection"""
        try:
            self._connection = psycopg.connect(
                self.config.get_connection_string()
            )
            logger.info("Database connection established")
            return self._connection
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            logger.info("Database connection closed")
    
    @contextmanager
    def get_cursor(self, row_factory=dict_row):
        """Context manager for database cursor"""
        conn = self.connect()
        cursor = conn.cursor(row_factory=row_factory)
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()
            self.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a SELECT query and return results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def insert_normalized_product(self, fingerprint: str, brand_name: str, 
                                  product_name: str, quantity: str = None, 
                                  category: str = None, vector: str = None) -> Optional[int]:
        """
        Insert a new normalized product
        Returns the ID of the inserted product, or existing ID if fingerprint exists
        """
        query = """
        INSERT INTO normalized_products (fingerprint, brand_name, product_name, quantity, category, vector)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (fingerprint) 
        DO UPDATE SET updated_at = CURRENT_TIMESTAMP
        RETURNING id;
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, (fingerprint, brand_name, product_name, quantity, category, vector))
                result = cursor.fetchone()
                return result['id'] if result else None
        except Exception as e:
            logger.error(f"Error inserting normalized product: {e}")
            raise
    
    def find_normalized_product_by_fingerprint(self, fingerprint: str) -> Optional[Dict]:
        """Find normalized product by fingerprint"""
        query = "SELECT * FROM normalized_products WHERE fingerprint = %s;"
        results = self.execute_query(query, (fingerprint,))
        return results[0] if results else None
    
    def find_normalized_products_by_brand(self, brand_name: str) -> List[Dict]:
        """Find all normalized products by brand name"""
        query = "SELECT * FROM normalized_products WHERE brand_name = %s;"
        return self.execute_query(query, (brand_name,))
    
    def insert_product(self, platform: str, brand_name: str, product_name: str,
                      mrp: float, product_id: int, price: float = None,
                      discount: float = 0, quantity: str = None, category: str = None,
                      image_url: str = '', platform_url: str = None,
                      available: bool = True, search: str = None) -> Optional[int]:
        """Insert a new product"""
        query = """
        INSERT INTO products (
            platform, platform_url, product_id, brand_name, product_name,
            mrp, price, discount, quantity, category, image_url, 
            available, search
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, (
                    platform, platform_url, product_id, brand_name, product_name,
                    mrp, price, discount, quantity, category, image_url,
                    available, search
                ))
                result = cursor.fetchone()
                return result['id'] if result else None
        except Exception as e:
            logger.error(f"Error inserting product: {e}")
            raise
    
    def bulk_insert_products(self, products: List[tuple]) -> int:
        """
        Bulk insert products
        products: List of tuples matching the product table structure
        Returns: Number of rows inserted
        """
        query = """
        INSERT INTO products (
            platform, platform_url, product_id, brand_name, product_name,
            mrp, price, discount, quantity, category, image_url, 
            available, search
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            with self.get_cursor() as cursor:
                cursor.executemany(query, products)
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error bulk inserting products: {e}")
            raise
    
    def get_all_normalized_products(self) -> List[Dict]:
        """Get all normalized products"""
        query = "SELECT * FROM normalized_products ORDER BY id;"
        return self.execute_query(query)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        # Count normalized products
        query = "SELECT COUNT(*) as count FROM normalized_products;"
        result = self.execute_query(query)
        stats['normalized_products_count'] = result[0]['count']
        
        # Count products
        query = "SELECT COUNT(*) as count FROM products;"
        result = self.execute_query(query)
        stats['products_count'] = result[0]['count']
        
        # Count by platform
        query = "SELECT platform, COUNT(*) as count FROM products GROUP BY platform;"
        stats['products_by_platform'] = self.execute_query(query)
        
        # Count by brand
        query = "SELECT brand_name, COUNT(*) as count FROM normalized_products GROUP BY brand_name ORDER BY count DESC LIMIT 10;"
        stats['top_brands'] = self.execute_query(query)
        
        return stats
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
                logger.info("Database connection test: SUCCESS")
                return result is not None
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Singleton instance
db_manager = DatabaseManager()


if __name__ == "__main__":
    # Test the database connection
    print("Testing database connection...")
    
    if db_manager.test_connection():
        print("✓ Database connection successful!")
        
        # Get statistics
        print("\nDatabase Statistics:")
        stats = db_manager.get_statistics()
        print(f"  Normalized Products: {stats['normalized_products_count']}")
        print(f"  Products: {stats['products_count']}")
        
        if stats['products_by_platform']:
            print("\n  Products by Platform:")
            for item in stats['products_by_platform']:
                print(f"    {item['platform']}: {item['count']}")
    else:
        print("✗ Database connection failed!")