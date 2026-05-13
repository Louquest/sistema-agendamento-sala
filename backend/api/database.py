import mysql.connector
from mysql.connector import pooling, Error
import os
import logging
from typing import Generator
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'salao_cabeleireira'),
    'charset': os.getenv('DB_CHARSET', 'utf8mb4'),
    'use_unicode': True,
    'autocommit': False,
    'connect_timeout': int(os.getenv('DB_TIMEOUT', 10)),
    'pool_name': 'salao_pool',
    'pool_size': int(os.getenv('DB_POOL_SIZE', 5)),
    'pool_reset_session': True
}

try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(**DB_CONFIG)
    logger.info(f"Pool de conexões criado com sucesso. Tamanho: {DB_CONFIG['pool_size']}")
except Error as e:
    logger.error(f"Erro ao criar pool de conexões: {e}")
    raise

def get_db() -> Generator:
    conn = None
    try:
        conn = connection_pool.get_connection()
        if not conn.is_connected():
            logger.warning("Conexão perdida, reconectando...")
            conn.reconnect()
        logger.debug("Conexão obtida do pool com sucesso")
        yield conn
    except Error as e:
        logger.error(f"Erro ao obter conexão do pool: {e}")
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()
            logger.debug("Conexão retornada ao pool")

@contextmanager
def get_db_cursor(dictionary: bool = True):
    conn = None
    cursor = None
    try:
        conn = connection_pool.get_connection()
        cursor = conn.cursor(dictionary=dictionary)
        yield cursor
        conn.commit()
    except Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Erro no cursor: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def test_connection() -> bool:
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                logger.info("Conexão com banco de dados testada com sucesso")
                return True
        return False
    except Error as e:
        logger.error(f"Falha no teste de conexão: {e}")
        return False

def get_db_status() -> dict:
    return {
        'pool_name': DB_CONFIG['pool_name'],
        'pool_size': DB_CONFIG['pool_size'],
        'is_connected': test_connection(),
        'config': {
            'host': DB_CONFIG['host'],
            'database': DB_CONFIG['database'],
            'user': DB_CONFIG['user']
        }
    }