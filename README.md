# Book2Skills 🏭

> **Agent 操作指南（Skills）生产工厂**

Book2Skills 是一个旨在将人类知识转化为 LLM Agent 易理解、可执行的专业技能包的自动化工具。本项目基于 [Mini-Agent](https://github.com/MiniMax-AI/Mini-Agent) 进行二次开发，在此对原项目作者表示衷心感谢！🙏

## 🎯 项目使命

我们为那群“嗷嗷待哺”的 **Agent 白板** 👶 提供成长的养料。通过将晦涩、冗长的专业文档自动“提炼”并“封装”成标准化的 Skills，让 Agent 能够快速掌握特定行业或领域的专家级操作能力。

---

## 🏗 项目架构

- **原材料 📚 (`library/`)**: 存放在这里的专业书籍、白皮书、API 文档、行业最佳实践等原始资料。
- **生产线 ⚙️**: 基于 LLM 的自动化处理流程，负责解析、总结并按照标准格式生成 Skill。
- **产品 📦 (`produced_skill/`)**: 最终产出的标准化 Skill 文件夹，每个文件夹包含核心的 `SKILL.md`（参考 [agent_skills_spec.md](skills/agent_skills_spec.md)）。

## 📁 目录结构

```text
.
├── book2skills/         # 核心源代码
│   ├── agent.py         # 主 Agent 循环
│   ├── cli.py           # 命令行接口
│   ├── config.py        # 配置加载
│   ├── llm/             # LLM 客户端
│   ├── tools/           # 工具实现
│   ├── utils/           # 辅助工具
│   ├── config/          # 内置配置模板
│   └── skills/          # 内置 Skill 库 (git submodule)
├── library/             # 原材料：存入专业书、文档等 (.txt, .md)
├── produced_skill/      # 产品：生成的 Agent Skills 包
├── tests/               # 测试套件
├── docs/                # 项目文档
├── workspace/           # Agent 工作临时文件夹
├── pyproject.toml       # 项目构建配置
└── README.md            # 项目自述文件
```

## 🛠 快速开始

### 🚀 快速运行 (用户模式)

1. **环境准备**:
   ```bash
   pip install -e .
   ```

2. **配置**:
   在 `~/.book2skills/config/config.yaml` 或项目根目录 `config/config.yaml` 中配置你的 API Key。

3. **生产技能**:
   ```bash
   book2skills --task "分析 library 目录下的量化投资书籍，并在 produced_skill 目录下生成相关的量化选股和时机选择技能包"
   ```

---

### 🔧 开发模式

此模式适合需要修改代码、添加功能或进行调试的开发者。

**安装与配置步骤：**

```bash
# 1. 克隆仓库
git clone https://github.com/fz/Book2Skills.git
cd Book2Skills

# 2. 安装 uv（如果尚未安装）
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell):
irm https://astral.sh/uv/install.ps1 | iex
# 安装后需要重启终端

# 3. 同步依赖
uv sync

# 4. 初始化示例 Skills（可选）
git submodule update --init --recursive

# 5. 复制配置模板
```

**macOS/Linux:**
```bash
cp config/config-example.yaml config/config.yaml
```

**Windows:**
```powershell
Copy-Item config\config-example.yaml config\config.yaml

# 6. 编辑配置文件
vim config/config.yaml  # 或使用您偏好的编辑器
```

填入您的 API Key 和对应的 API Base：

```yaml
api_key: "YOUR_API_KEY_HERE"          # 填入您的 API Key
api_base: "https://api.minimax.io"     # 默认使用海外版，国内版请修改为 https://api.minimaxi.com
model: "MiniMax-M2.5"
max_steps: 100
workspace_dir: "./workspace"
```

> 📖 完整的配置指南，请参阅 [config-example.yaml](config/config-example.yaml)

**运行方式：**

选择您偏好的方式运行：

```bash
# 方式 1：作为模块直接运行（适合调试）
uv run python -m cli

# 方式 2：以可编辑模式安装（推荐）
uv tool install -e .
# 安装后，您可以在任何路径下运行，且代码更改会立即生效
book2skills
book2skills --workspace /path/to/your/project
```

## 📜 Skill 规范

产出的 Skill 遵循 [Agent Skills Spec](skills/agent_skills_spec.md) 维护。
一个典型的 Skill 包含：
- `name`: 技能唯一标识
- `description`: 技能描述及 Agent 激活时机
- `Markdown Content`: 具体的行动指南与行业沉淀

## 🤝 致谢

本项目核心代码逻辑参考并改进自 [Mini-Agent](https://github.com/MiniMax-AI/Mini-Agent)。Mini-Agent 为我们提供了一个极佳的轻量级 Agent 运行环境，在此基础上我们增加了专门针对知识蒸馏与 Skill 生产的逻辑。

---
Produced with ❤️ for the next generation of AI Agents.
