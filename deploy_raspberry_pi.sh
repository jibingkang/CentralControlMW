#!/bin/bash

#========================================
# 中央控制中间件 - 树莓派部署脚本
# 作者: AI Assistant
# 日期: 2026-04-20
#========================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_DIR="/home/pi/esls/CentralControlMW"

# 数据库配置
DB_HOST="localhost"
DB_PORT="3306"
DB_NAME="db_centralcontrolmw"
DB_USER="eslsdb"
DB_PASSWORD="eslsdb@pi"

# 服务配置
SERVICE_NAME="centralcontrolmw"
SERVICE_USER="pi"
SERVICE_PORT="8000"

# 解析命令行参数
if [ $# -eq 1 ]; then
    # 直接传入端口号
    SERVICE_PORT="$1"
elif [ $# -eq 2 ]; then
    # 使用 -p 选项传入端口号
    if [ "$1" = "-p" ]; then
        SERVICE_PORT="$2"
    else
        echo "用法: $0 [端口号] 或 $0 [-p 端口号]"
        exit 1
    fi
fi

# 显示端口信息
echo -e "${YELLOW}[INFO]${NC} 服务端口: ${SERVICE_PORT}"

# 输出带颜色的信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "请使用 root 用户或 sudo 执行此脚本"
        exit 1
    fi
}

# 检查项目目录
check_project() {
    if [ ! -d "$PROJECT_DIR" ]; then
        error "项目目录不存在: $PROJECT_DIR"
        info "请先执行: git clone https://github.com/jibingkang/CentralControlMW.git $PROJECT_DIR"
        exit 1
    fi
    info "项目目录检查通过: $PROJECT_DIR"
}

# 安装系统依赖
install_system_deps() {
    info "安装系统依赖..."
    apt update
    apt install -y python3 python3-pip python3-venv
    info "系统依赖安装完成"
}

# 创建虚拟环境
create_venv() {
    info "创建Python虚拟环境..."
    cd "$PROJECT_DIR"

    if [ -d "venv" ]; then
        warn "虚拟环境已存在，跳过创建"
    else
        python3 -m venv venv
        info "虚拟环境创建完成"
    fi
}

# 安装Python依赖
install_python_deps() {
    info "安装Python依赖..."
    cd "$PROJECT_DIR"
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    info "Python依赖安装完成"
}

# 配置数据库
setup_database() {
    info "配置数据库..."

    # 创建数据库
    mysql -u root -p <<EOF
CREATE DATABASE IF NOT EXISTS ${DB_NAME} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'%';
FLUSH PRIVILEGES;
EOF

    info "数据库配置完成"
}

# 初始化数据库表
init_database() {
    info "初始化数据库表..."
    cd "$PROJECT_DIR"

    if [ -f "db_init/init.sql" ]; then
        mysql -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < db_init/init.sql
        info "数据库表初始化完成"
    else
        warn "未找到初始化脚本: db_init/init.sql"
    fi
}

# 配置.env文件
setup_env() {
    info "配置环境变量文件..."
    cd "$PROJECT_DIR"

    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            info "已从 .env.example 创建 .env 文件"
        else
            cat > .env <<EOF
# 数据库配置
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}

# TCP服务器配置
TCP_SERVER_HOST=192.168.1.200
TCP_SERVER_PORT=9999

# 服务配置
HOST=0.0.0.0
PORT=${SERVICE_PORT}
EOF
            info "已创建 .env 文件"
        fi
    else
        # 更新已存在的 .env 文件中的端口配置
        if grep -q "^PORT=" .env; then
            sed -i "s/^PORT=.*/PORT=${SERVICE_PORT}/" .env
            info "已更新 .env 文件中的端口配置"
        else
            echo "\n# 服务配置\nHOST=0.0.0.0\nPORT=${SERVICE_PORT}" >> .env
            info "已添加端口配置到 .env 文件"
        fi
    fi
}

# 创建systemd服务
create_service() {
    info "创建systemd服务..."
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=Central Control Middleware
After=network.target mysql.service
Wants=mysql.service

[Service]
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/venv/bin/python ${PROJECT_DIR}/run.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
# 避免服务无限重启
StartLimitIntervalSec=60
StartLimitBurst=3

[Install]
WantedBy=multi-user.target
EOF

    info "systemd服务文件创建完成"
}

# 检查端口是否被占用
check_port() {
    if lsof -i :${SERVICE_PORT} > /dev/null 2>&1; then
        warn "端口 ${SERVICE_PORT} 已被占用，尝试停止占用该端口的进程..."
        lsof -ti :${SERVICE_PORT} | xargs -r kill -9
        sleep 2
    fi
    info "端口 ${SERVICE_PORT} 检查完成"
}

# 启动服务
start_service() {
    info "启动服务..."

    # 检查端口占用
    check_port

    # 重新加载systemd配置
    systemctl daemon-reload

    # 启动服务
    systemctl start ${SERVICE_NAME}

    # 启用自启动
    systemctl enable ${SERVICE_NAME}

    info "服务已启动并设置自启动"
}

# 验证服务状态
verify_service() {
    info "验证服务状态..."
    
    sleep 3
    
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        info "服务运行正常！"
        
        echo ""
        echo "========================================"
        echo -e "${GREEN}部署完成！${NC}"
        echo "========================================"
        echo ""
        echo "服务地址: http://$(hostname -I | awk '{print $1}'):${SERVICE_PORT}"
        echo "前端页面: http://$(hostname -I | awk '{print $1}'):${SERVICE_PORT}/index.html"
        echo ""
        echo "常用命令:"
        echo "  查看服务状态: sudo systemctl status ${SERVICE_NAME}"
        echo "  查看服务日志: sudo journalctl -u ${SERVICE_NAME} -f"
        echo "  重启服务: sudo systemctl restart ${SERVICE_NAME}"
        echo "  停止服务: sudo systemctl stop ${SERVICE_NAME}"
        echo "  禁用自启动: sudo systemctl disable ${SERVICE_NAME}"
        echo ""
    else
        error "服务启动失败，请检查日志"
        info "查看日志: sudo journalctl -u ${SERVICE_NAME} -n 50"
        exit 1
    fi
}

# 主函数
main() {
    echo ""
    echo "========================================"
    echo "  中央控制中间件 - 树莓派部署脚本"
    echo "========================================"
    echo ""

    check_root
    check_project
    install_system_deps
    create_venv
    install_python_deps
    setup_database
    init_database
    setup_env
    create_service
    start_service
    verify_service
}

# 执行主函数
main "$@"
