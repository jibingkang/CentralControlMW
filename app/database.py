from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

Base = declarative_base()

# 导入所有模型，确保它们被注册
from app.models import DeviceMapping, SystemConfig, OperationLog

# 数据库连接状态
db_connection_status = {
    "connected": False,
    "error": None,
    "last_checked": None
}

# 尝试创建数据库引擎
try:
    logger.info(f"正在连接数据库: {settings.DB_HOST}:{settings.DB_PORT}")
    logger.info(f"数据库URL: {settings.DATABASE_URL}")
    
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        pool_recycle=settings.DB_POOL_RECYCLE
    )
    
    # 测试数据库连接
    logger.info("开始测试数据库连接...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        logger.info(f"数据库连接测试结果: {result.scalar()}")
    
    # 自动创建表结构
    logger.info("开始创建表结构...")
    Base.metadata.create_all(bind=engine)
    logger.info("表结构创建完成！")
    
    # 初始化系统配置
    logger.info("开始初始化系统配置...")
    with engine.connect() as conn:
        # 检查system_config表是否有数据
        result = conn.execute(text("SELECT COUNT(*) FROM system_config"))
        count = result.scalar()
        
        if count == 0:
            # 插入初始配置
            conn.execute(text(""" 
                INSERT INTO system_config (config_key, config_value, description) VALUES
                ('tcp_server_host', '192.168.1.200', 'TCP服务器地址'),
                ('tcp_server_port', '8080', 'TCP服务器端口')
            """))
            conn.commit()
            logger.info("系统配置初始化完成！")
        else:
            logger.info("系统配置已存在，跳过初始化")
    
    db_connection_status["connected"] = True
    db_connection_status["error"] = None
    db_connection_status["last_checked"] = time.time()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("数据库连接成功！")
except Exception as e:
    error_msg = str(e)
    db_connection_status["connected"] = False
    db_connection_status["error"] = error_msg
    db_connection_status["last_checked"] = time.time()
    logger.error(f"数据库连接失败: {error_msg}")
    # 数据库连接失败时，创建一个mock session
    class MockSession:
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        
        def query(self, *args, **kwargs):
            class MockQuery:
                def all(self):
                    return []
                
                def first(self):
                    return None
                
                def filter(self, *args, **kwargs):
                    return self
                
                def count(self):
                    return 0
                
                def offset(self, *args, **kwargs):
                    return self
                
                def limit(self, *args, **kwargs):
                    return self
            return MockQuery()
        
        def add(self, *args, **kwargs):
            pass
        
        def commit(self):
            pass
        
        def delete(self, *args, **kwargs):
            pass
    
    SessionLocal = MockSession


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        if hasattr(db, 'close'):
            db.close()


def get_db_status():
    """获取数据库连接状态"""
    return db_connection_status


def update_db_config(host=None, port=None, user=None, password=None, db_name=None):
    """更新数据库配置"""
    global engine, SessionLocal, db_connection_status
    try:
        from app.config import settings
        
        # 保存配置到数据库的system_config表（使用旧的数据库连接）
        try:
            with engine.connect() as conn:
                # 更新数据库主机
                if host:
                    conn.execute(text("""
                        INSERT INTO system_config (config_key, config_value, description)
                        VALUES ('db_host', :host, '数据库主机地址')
                        ON DUPLICATE KEY UPDATE config_value = :host
                    """), {"host": host})

                # 更新数据库端口
                if port:
                    conn.execute(text("""
                        INSERT INTO system_config (config_key, config_value, description)
                        VALUES ('db_port', :port, '数据库端口')
                        ON DUPLICATE KEY UPDATE config_value = :port
                    """), {"port": str(port)})

                # 更新数据库用户名
                if user:
                    conn.execute(text("""
                        INSERT INTO system_config (config_key, config_value, description)
                        VALUES ('db_user', :user, '数据库用户名')
                        ON DUPLICATE KEY UPDATE config_value = :user
                    """), {"user": user})

                # 更新数据库密码
                if password:
                    conn.execute(text("""
                        INSERT INTO system_config (config_key, config_value, description)
                        VALUES ('db_password', :password, '数据库密码')
                        ON DUPLICATE KEY UPDATE config_value = :password
                    """), {"password": password})

                # 更新数据库名
                if db_name:
                    conn.execute(text("""
                        INSERT INTO system_config (config_key, config_value, description)
                        VALUES ('db_name', :db_name, '数据库名称')
                        ON DUPLICATE KEY UPDATE config_value = :db_name
                    """), {"db_name": db_name})

                conn.commit()
                logger.info("数据库配置已保存到system_config表")
        except Exception as e:
            logger.warning(f"保存配置到数据库失败: {str(e)}")
        
        # 更新settings对象
        if host:
            settings.DB_HOST = host
        if port:
            settings.DB_PORT = port
        if user:
            settings.DB_USER = user
        if password:
            settings.DB_PASSWORD = password
        if db_name:
            settings.DB_NAME = db_name
        
        # 同步更新.env文件
        try:
            import os
            env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
            
            if os.path.exists(env_file):
                with open(env_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 更新.env文件中的配置
                with open(env_file, 'w', encoding='utf-8') as f:
                    for line in lines:
                        if line.startswith('DB_HOST=') and host:
                            f.write(f'DB_HOST={host}\n')
                        elif line.startswith('DB_PORT=') and port:
                            f.write(f'DB_PORT={port}\n')
                        elif line.startswith('DB_USER=') and user:
                            f.write(f'DB_USER={user}\n')
                        elif line.startswith('DB_PASSWORD=') and password:
                            f.write(f'DB_PASSWORD={password}\n')
                        elif line.startswith('DB_NAME=') and db_name:
                            f.write(f'DB_NAME={db_name}\n')
                        else:
                            f.write(line)
                logger.info(f".env文件已更新: {env_file}")
            else:
                logger.warning(f".env文件不存在: {env_file}")
        except Exception as e:
            logger.warning(f"更新.env文件失败: {str(e)}")
        
        # 重建数据库引擎
        logger.info(f"更新数据库配置: host={host}, port={port}, user={user}, db_name={db_name}")
        
        # 关闭旧连接
        if 'engine' in globals() and engine:
            engine.dispose()
        
        # 创建新的数据库引擎
        engine = create_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            pool_recycle=settings.DB_POOL_RECYCLE
        )
        
        # 测试连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"数据库连接测试结果: {result.scalar()}")
        
        # 自动创建表结构
        Base.metadata.create_all(bind=engine)
        
        # 重建会话工厂
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # 更新连接状态
        db_connection_status["connected"] = True
        db_connection_status["error"] = None
        db_connection_status["last_checked"] = time.time()
        
        logger.info("数据库配置更新成功")
        return True
    except Exception as e:
        error_msg = str(e)
        db_connection_status["connected"] = False
        db_connection_status["error"] = error_msg
        db_connection_status["last_checked"] = time.time()
        logger.error(f"更新数据库配置失败: {error_msg}")
        return False
