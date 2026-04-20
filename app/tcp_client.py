import socket
import time
import logging
from app.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# TCP连接状态
tcp_connection_status = {
    "connected": False,
    "error": None,
    "last_checked": None,
    "last_sent": None,
    "server": {
        "host": settings.TCP_SERVER_HOST,
        "port": settings.TCP_SERVER_PORT
    }
}

# 全局TCP连接对象（可选，用于长连接）
_tcp_socket = None

def send_tcp_message(host: str, port: int, message: str) -> bool:
    """发送TCP消息"""
    global tcp_connection_status
    
    try:
        logger.info(f"开始发送TCP消息到 {host}:{port}")
        logger.info(f"发送消息: {message}")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(settings.TCP_TIMEOUT)
            s.connect((host, port))
            s.sendall(message.encode('utf-8'))
            # 接收响应（可选）
            # response = s.recv(1024)
            # logger.info(f"收到响应: {response.decode('utf-8')}")
        
        tcp_connection_status["connected"] = True
        tcp_connection_status["error"] = None
        tcp_connection_status["last_checked"] = time.time()
        tcp_connection_status["last_sent"] = time.time()
        tcp_connection_status["server"]["host"] = host
        tcp_connection_status["server"]["port"] = port
        
        logger.info(f"TCP消息发送成功到 {host}:{port}")
        return True
    except Exception as e:
        error_msg = str(e)
        tcp_connection_status["connected"] = False
        tcp_connection_status["error"] = error_msg
        tcp_connection_status["last_checked"] = time.time()
        logger.error(f"TCP消息发送失败: {error_msg}")
        return False

def check_tcp_connection(host: str, port: int) -> bool:
    """检查TCP连接"""
    global tcp_connection_status
    
    try:
        logger.info(f"开始检查TCP连接: {host}:{port}")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(settings.TCP_TIMEOUT)
            s.connect((host, port))
        
        tcp_connection_status["connected"] = True
        tcp_connection_status["error"] = None
        tcp_connection_status["last_checked"] = time.time()
        tcp_connection_status["server"]["host"] = host
        tcp_connection_status["server"]["port"] = port
        
        logger.info(f"TCP连接检查成功: {host}:{port}")
        return True
    except Exception as e:
        error_msg = str(e)
        tcp_connection_status["connected"] = False
        tcp_connection_status["error"] = error_msg
        tcp_connection_status["last_checked"] = time.time()
        logger.error(f"TCP连接检查失败: {error_msg}")
        return False

def reconnect_tcp(host: str, port: int) -> bool:
    """重新连接TCP"""
    global _tcp_socket
    
    try:
        logger.info(f"开始重新连接TCP: {host}:{port}")
        
        # 关闭旧连接
        if _tcp_socket:
            try:
                _tcp_socket.close()
                logger.info("旧TCP连接已关闭")
            except:
                pass
        
        # 创建新连接
        _tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _tcp_socket.settimeout(settings.TCP_TIMEOUT)
        _tcp_socket.connect((host, port))
        
        tcp_connection_status["connected"] = True
        tcp_connection_status["error"] = None
        tcp_connection_status["last_checked"] = time.time()
        tcp_connection_status["server"]["host"] = host
        tcp_connection_status["server"]["port"] = port
        
        logger.info(f"TCP重新连接成功: {host}:{port}")
        return True
    except Exception as e:
        error_msg = str(e)
        tcp_connection_status["connected"] = False
        tcp_connection_status["error"] = error_msg
        tcp_connection_status["last_checked"] = time.time()
        logger.error(f"TCP重新连接失败: {error_msg}")
        return False

def send_custom_message(host: str, port: int, message: str) -> dict:
    """发送自定义TCP消息（用于测试）"""
    start_time = time.time()
    success = send_tcp_message(host, port, message)
    end_time = time.time()
    
    return {
        "success": success,
        "host": host,
        "port": port,
        "message": message,
        "time_taken": round(end_time - start_time, 3),
        "status": tcp_connection_status
    }

def get_tcp_status():
    """获取TCP连接状态"""
    return tcp_connection_status

def close_tcp_connection():
    """关闭TCP连接"""
    global _tcp_socket
    try:
        if _tcp_socket:
            _tcp_socket.close()
            _tcp_socket = None
            tcp_connection_status["connected"] = False
            logger.info("TCP连接已关闭")
            return True
    except Exception as e:
        logger.error(f"关闭TCP连接失败: {str(e)}")
    return False
