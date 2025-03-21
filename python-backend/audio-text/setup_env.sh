#!/bin/bash
# 短视频升级营销项目环境配置脚本

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${BLUE}[信息]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查Python版本
check_python_version() {
    print_info "检查Python版本..."
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    
    if [[ -z "$python_version" ]]; then
        print_error "未找到Python3，请先安装Python3"
        exit 1
    fi
    
    print_success "Python版本: $python_version"
}

# 创建虚拟环境
create_venv() {
    print_info "创建Python虚拟环境..."
    
    if [ -d "venv" ]; then
        print_warning "虚拟环境已存在，跳过创建步骤"
    else
        python3 -m venv venv
        if [ $? -eq 0 ]; then
            print_success "虚拟环境创建成功"
        else
            print_error "虚拟环境创建失败"
            exit 1
        fi
    fi
}

# 激活虚拟环境
activate_venv() {
    print_info "激活虚拟环境..."
    source venv/bin/activate
    
    if [ $? -eq 0 ]; then
        print_success "虚拟环境激活成功"
    else
        print_error "虚拟环境激活失败"
        exit 1
    fi
}

# 安装依赖
install_dependencies() {
    print_info "安装依赖..."
    
    # 升级pip
    print_info "升级pip..."
    pip install --upgrade pip
    
    # 安装核心依赖
    print_info "安装核心依赖..."
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        print_success "核心依赖安装成功"
    else
        print_error "核心依赖安装失败"
        exit 1
    fi
    
    # 安装阿里云NLS SDK
    print_info "安装阿里云NLS SDK..."
    mkdir -p temp_download
    cd temp_download
    
    print_info "下载阿里云NLS SDK..."
    curl -O https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241203/tbjics/alibabacloud-nls-python-sdk-dev-20241203.zip
    if [ $? -ne 0 ]; then
        print_error "下载阿里云NLS SDK失败"
        cd ..
    else
        print_success "下载阿里云NLS SDK成功"
        
        print_info "解压SDK..."
        unzip -o alibabacloud-nls-python-sdk-dev-20241203.zip
        if [ $? -ne 0 ]; then
            print_error "解压SDK失败"
            cd ..
        else
            print_success "解压SDK成功"
            
            print_info "安装SDK..."
            cd alibabacloud-nls-python-sdk-dev
            pip install .
            if [ $? -ne 0 ]; then
                print_error "安装SDK失败"
            else
                print_success "安装SDK成功"
            fi
            cd ../..
        fi
    fi
    
    # 尝试安装可选依赖pydub
    print_info "尝试安装可选依赖pydub..."
    pip install pydub
    
    if [ $? -eq 0 ]; then
        print_success "pydub安装成功"
    else
        print_warning "pydub安装失败，这在Python 3.13中是正常的，程序将使用替代方案"
    fi
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    
    # 创建recordings目录
    if [ ! -d "recordings" ]; then
        mkdir -p recordings
        print_success "创建recordings目录"
    fi
    
    # 创建output目录
    if [ ! -d "output" ]; then
        mkdir -p output
        print_success "创建output目录"
    fi
    
    # 创建audio_files目录
    if [ ! -d "audio_files" ]; then
        mkdir -p audio_files
        print_success "创建audio_files目录"
    fi
    
    # 创建transcripts目录
    if [ ! -d "transcripts" ]; then
        mkdir -p transcripts
        print_success "创建transcripts目录"
    fi
    
    # 创建generated_content目录
    if [ ! -d "generated_content" ]; then
        mkdir -p generated_content
        print_success "创建generated_content目录"
    fi
}

# 检查环境配置
check_env() {
    print_info "检查环境配置..."
    
    # 运行测试脚本
    python test_env.py
    
    if [ $? -eq 0 ]; then
        print_success "环境配置检查通过"
    else
        print_warning "环境配置检查发现问题，但程序可能仍然可以运行"
    fi
}

# 主函数
main() {
    echo "=================================================="
    echo "    短视频升级营销项目环境配置脚本"
    echo "=================================================="
    
    check_python_version
    create_venv
    activate_venv
    install_dependencies
    create_directories
    check_env
    
    echo ""
    print_success "环境配置完成！"
    echo ""
    echo "使用说明:"
    echo "1. 激活虚拟环境: source venv/bin/activate"
    echo "2. 运行程序: python main.py [命令] [参数]"
    echo "3. 查看帮助: python main.py --help"
    echo "4. 退出虚拟环境: deactivate"
    echo ""
    echo "详细文档请参考: docs/使用说明.md"
    echo "=================================================="
}

# 执行主函数
main
