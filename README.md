# GSV2P TTS 插件

基于 GSV2P API 的文本转语音插件，支持多种语言和音色。

## 功能特性

- 🎤 文本转语音合成
- 🌍 支持中文、英文、日文等多种语言
- 🎭 多种音色选择
- ⚙️ 丰富的语音合成参数配置
- 🔄 自动触发（Action）和手动触发（Command）两种模式

## 使用方法

### 1. 自动触发（关键词）

当消息中包含以下关键词时自动触发：
- `语音`、`说话`、`朗读`、`念出来`、`用语音说`
- `gsv2p`、`tts`

**示例：**
```
用户：用语音说"你好"
机器人：[发送语音消息]
```

### 2. 手动命令

使用 `/gsv2p` 命令手动触发：

```bash
# 基本用法（使用默认音色）
/gsv2p 你好，世界！

# 指定音色
/gsv2p 今天天气不错 原神-中文-派蒙_ZH

# 日文示例
/gsv2p こんにちは
```

## 配置说明

编辑 `config.toml` 文件进行配置：

### 必需配置

```toml
[gsv2p]
# API Token（必须配置）
api_token = "your_api_token_here"

# 默认音色（必须配置）
default_voice = "原神-中文-派蒙_ZH"
```

### 可选配置

```toml
[gsv2p]
# API 地址
api_url = "https://gsv2p.acgnai.top/v1/audio/speech"

# 请求超时时间（秒）
timeout = 30

# 语音速度（0.5-2.0）
speed = 1.0

# 文本语言
text_lang = "中英混合"  # 可选: 中文/英文/日文/中英混合

# 情感设置
emotion = "默认"

# 高级参数
temperature = 1.0      # 温度参数（0-1）
top_k = 10            # Top-K 采样
top_p = 1.0           # Top-P 采样
```

### 组件控制

```toml
[components]
# 是否启用自动触发
action_enabled = true

# 是否启用手动命令
command_enabled = true
```

## 音频文件

生成的音频文件保存在项目根目录：
```
/path/to/MaiBot/gsv2p_tts_output.mp3
```

## 获取 API Token

访问 [GSV2P API](https://tts.acgnai.top) 注册并获取 API Token。

## 常见音色列表

- `原神-中文-派蒙_ZH`
- `原神-中文-甘雨_ZH`
- `原神-中文-胡桃_ZH`
- `原神-中文-雷电将军_ZH`
- 更多音色请查询 API 文档

## 高级配置参数

### 文本处理

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `text_split_method` | `"按标点符号切"` | 文本分割方法 |
| `batch_size` | `1` | 批处理大小 |
| `batch_threshold` | `0.75` | 批处理阈值 |
| `fragment_interval` | `0.3` | 片段间隔（秒） |

### 采样参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `top_k` | `10` | Top-K 采样 |
| `top_p` | `1.0` | Top-P 采样 |
| `temperature` | `1.0` | 温度参数 |
| `repetition_penalty` | `1.35` | 重复惩罚 |
| `sample_steps` | `16` | 采样步数 |
| `seed` | `-1` | 随机种子（-1为随机） |

### 推理设置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `parallel_infer` | `true` | 是否并行推理 |
| `split_bucket` | `true` | 是否分桶 |
| `if_sr` | `false` | 是否超分辨率 |

## 故障排除

### 常见问题

1. **API Token 错误**
   - 确保在配置文件中正确设置了 `api_token`
   - 检查 Token 是否有效且未过期

2. **网络连接问题**
   - 检查网络连接是否正常
   - 适当增加 `timeout` 值

3. **音频生成失败**
   - 检查文本内容是否合法
   - 确认音色参数是否正确
   - 查看日志获取详细错误信息

## 依赖项

- Python 3.8+
- aiohttp

## 版本信息

- **版本**：1.0.0
- **作者**：Augment Agent

## 致谢

- GPT-SoVITS 开发者：@花儿不哭
- 模型训练者：@红血球AE3803 @白菜工厂1145号员工
- 推理特化包适配 & 在线推理：@AI-Hobbyist

## 许可证

详见 LICENSE 文件
