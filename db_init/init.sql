-- 数据库名: db_centralcontrolmw

CREATE DATABASE IF NOT EXISTS db_centralcontrolmw DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE db_centralcontrolmw;

-- 设备ID与转换码绑定表
CREATE TABLE IF NOT EXISTS device_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL UNIQUE COMMENT '设备ID，如 92.95.40.81',
    convert_code VARCHAR(100) NOT NULL COMMENT '转换码，如 0E 99 EE 22 25',
    description VARCHAR(200) DEFAULT '' COMMENT '描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备ID与转换码绑定表';

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value VARCHAR(200) NOT NULL,
    description VARCHAR(200) DEFAULT '',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- 初始配置
INSERT INTO system_config (config_key, config_value, description) VALUES
('tcp_server_host', '192.168.1.200', 'TCP服务器地址'),
('tcp_server_port', '8080', 'TCP服务器端口')
ON DUPLICATE KEY UPDATE config_value=VALUES(config_value);

-- 操作日志表
CREATE TABLE IF NOT EXISTS operation_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    log_type VARCHAR(20) NOT NULL COMMENT '日志类型: callback-按键回调, mapping-映射操作, config-配置变更',
    device_id VARCHAR(50) DEFAULT '' COMMENT '设备ID',
    convert_code VARCHAR(100) DEFAULT '' COMMENT '转换码',
    request_data TEXT COMMENT '请求数据JSON',
    response_data TEXT COMMENT '响应数据JSON',
    status VARCHAR(20) NOT NULL COMMENT '状态: success-成功, failed-失败',
    error_message TEXT COMMENT '错误信息',
    client_ip VARCHAR(50) DEFAULT '' COMMENT '客户端IP',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_operation_log_type (log_type),
    INDEX idx_operation_log_device_id (device_id),
    INDEX idx_operation_log_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';
