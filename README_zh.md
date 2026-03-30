# DataYee

单分子力谱（SMFS）数据分析工具

[English](README.md) | [中文](README_zh.md)

## 简介

DataYee 是一款基于 Python 的桌面应用程序，用于分析单分子力谱（SMFS）数据，通常使用原子力显微镜（AFM）获取。它提供力曲线处理、WLC（蠕虫链）拟合、能量景观分析等功能。

## 功能特点

- **力曲线处理**：加载、处理和可视化来自 JPK、TXT 和 DataYee 格式的力-距离曲线
- **峰值检测**：自动和手动检测解折叠峰值
- **WLC 拟合**：蠕虫链模型拟合，估算轮廓长度和持久长度
- **能量景观分析**：使用 Bell-Evans 和 Friddle 模型计算解折叠能量
- **数据聚类**：K-Means 聚类和基于 DTW 的相似性排序
- **批量处理**：同时处理多条力曲线
- **导出选项**：导出为 Excel、TXT 和图像格式

## 安装

### 环境要求

- Python 3.11+
- Conda 或 pip 包管理器

### 快速安装

```bash
# 克隆仓库
git clone https://github.com/Andachten/DataYee.git
cd DataYee

# 创建 conda 环境
conda create -n datayee python=3.11 -y
conda activate datayee

# 安装依赖
pip install numpy pandas scipy matplotlib scikit-learn PyQt5 openpyxl xlwt

# 运行程序
python -m src
```

## 使用方法

### 启动程序

```bash
# 从源码运行
python -m src

# 或指定文件
python -m src path/to/force_curve.jpk-force
```

### 基本工作流程

1. **加载力曲线**：文件 → 打开力曲线（或拖放）
2. **处理数据**：使用自动步骤或手动调整参数
3. **检测峰值**：点击峰值或使用自动检测
4. **WLC 拟合**：调整 lc、lp 参数并拟合曲线
5. **能量分析**：计算解折叠力和能量景观
6. **导出结果**：导出为 Excel、TXT 或图像

### 命令行选项

```bash
python -m src --help
```

## 项目结构

```
DataYee/
├── src/
│   ├── __main__.py          # 入口点
│   ├── cli.py               # 命令行接口
│   ├── main.py              # 核心程序逻辑
│   ├── update.py            # 自动更新检查
│   ├── designer.py          # Qt UI 定义
│   ├── core/                # 核心算法
│   │   ├── data_processing.py
│   │   ├── fitting.py
│   │   ├── clustering.py
│   │   └── file_io.py
│   ├── models/              # 数据模型
│   │   └── force_curve.py
│   └── ui/                  # UI 组件
│       ├── main_window.py
│       ├── dialogs/
│       └── widgets/
├── tests/                   # 测试套件
├── scripts/                 # 用户脚本
├── testdata/                # 测试数据
└── pyproject.toml          # 项目配置
```

## 开发

### 运行测试

```bash
pytest tests/ -v
```

### 代码质量检查

```bash
# 使用 ruff 检查
ruff check src/

# 使用 mypy 类型检查
mypy src/
```

## 依赖

- **numpy**: 数值计算
- **pandas**: 数据处理
- **scipy**: 科学计算
- **matplotlib**: 绘图和可视化
- **scikit-learn**: 机器学习和聚类
- **PyQt5**: GUI 框架
- **openpyxl/xlwt**: Excel 文件支持

## 参与贡献

欢迎贡献代码！请提交 issues 或 pull requests。

## 许可证

MIT 许可证

## 引用

如果您在研究中使用了 DataYee，请引用：

```
DataYee: 单分子力谱数据分析工具
https://github.com/Andachten/DataYee
```

## 支持

- **问题反馈**：https://github.com/Andachten/DataYee/issues

## 致谢

为单分子力谱研究开发。
