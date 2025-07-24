# GSV2P TTS 插件

基于 GSV2P API 的文本转语音插件，支持多种语言和高级语音合成参数。

## 功能特性

- 🎵 **高质量语音合成**：基于先进的GSV2P TTS模型
- 🌍 **多语言支持**：支持中文、英文、中英混合等多种语言
- 🎛️ **丰富参数配置**：支持语音速度、情感、温度等多种参数调节
- 🎭 **多音色选择**：支持多种音色配置，默认使用"原神-中文-派蒙_ZH"
- 🤖 **智能触发**：支持关键词自动触发和命令手动触发两种模式
- ⚙️ **灵活配置**：支持配置文件自定义所有参数
- 🔧 **高级语音合成**：支持批处理、并行推理、超分辨率等高级功能

## 安装配置

### 1. 依赖安装

插件需要以下Python依赖：
```bash
pip install aiohttp
```

### 2. 配置API Token

在 `config.toml` 文件中设置您的API Token：

**获取Token地址：** https://tts.acgnai.top/

```toml
[gsv2p]
api_token = "your_api_token_here"
```

### 3. 配置音色

设置默认音色（推荐）：

```toml
[gsv2p]
default_voice = "原神-中文-派蒙_ZH"
```

## 使用方法

### Action触发（自动模式）

当消息中包含以下关键词时，插件会自动触发语音合成：
- "语音"、"说话"、"朗读"
- "念出来"、"用语音说"
- "gsv2p"、"tts"

**关键词匹配特性：**
- 不区分大小写
- 支持关键词在消息中任意位置出现
- 自动提取需要转换的文本内容

**使用示例：**
```
用户：请用语音说"你好世界"
机器人：[自动生成语音文件并发送]

用户：帮我朗读这段文字：今天天气很好
机器人：[自动生成语音文件并发送]
```

### Command触发（手动模式）

使用 `/gsv2p` 命令手动触发语音合成：

**命令格式：**
```
/gsv2p 文本内容 [音色]
```

**命令特性：**
- 支持正则表达式匹配
- 音色参数可选，未指定时使用默认音色
- 会拦截原始消息，不会显示命令本身

**使用示例：**
```
/gsv2p 你好，世界！
/gsv2p 今天天气不错 原神-中文-派蒙_ZH
/gsv2p こんにちは voice2
```

## 配置参数

### 插件控制配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `plugin.enabled` | bool | `true` | 是否启用插件 |
| `components.action_enabled` | bool | `true` | 是否启用Action组件（自动触发） |
| `components.command_enabled` | bool | `true` | 是否启用Command组件（手动触发） |

### 基础配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `api_url` | string | `https://gsv2p.acgnai.top/v1/audio/speech` | GSV2P API地址 |
| `api_token` | string | `""` | API认证Token（必须设置） |
| `default_voice` | string | `"原神-中文-派蒙_ZH"` | 默认音色 |
| `timeout` | int | `30` | 请求超时时间（秒） |

### 语音合成参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model` | string | `"tts-v4"` | TTS模型版本 |
| `response_format` | string | `"mp3"` | 音频输出格式 |
| `speed` | float | `1.0` | 语音播放速度 |
| `text_lang` | string | `"中英混合"` | 文本语言类型 |
| `prompt_lang` | string | `"中文"` | 提示语言 |
| `emotion` | string | `"默认"` | 情感表达 |

### 高级采样参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `top_k` | int | `10` | Top-K采样参数，控制候选词数量 |
| `top_p` | float | `1.0` | Top-P采样参数，控制累积概率 |
| `temperature` | float | `1.0` | 温度参数，控制随机性 |
| `repetition_penalty` | float | `1.35` | 重复惩罚系数，避免重复 |
| `sample_steps` | int | `16` | 采样步数，影响质量 |
| `seed` | int | `-1` | 随机种子（-1为随机） |

### 文本处理参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `text_split_method` | string | `"按标点符号切"` | 文本分割方法 |
| `batch_size` | int | `1` | 批处理大小 |
| `batch_threshold` | float | `0.75` | 批处理阈值 |
| `split_bucket` | bool | `true` | 是否启用分桶处理 |
| `fragment_interval` | float | `0.3` | 音频片段间隔（秒） |
| `parallel_infer` | bool | `true` | 是否启用并行推理 |
| `if_sr` | bool | `false` | 是否启用超分辨率处理 |

## 完整配置示例

```toml
# GSV2P TTS插件配置文件

# 插件基本配置
[plugin]
enabled = true

# 组件启用控制
[components]
action_enabled = true   # 启用Action组件（自动触发）
command_enabled = true  # 启用Command组件（手动触发）

# GSV2P API配置
[gsv2p]
# 基础配置
api_url = "https://gsv2p.acgnai.top/v1/audio/speech"
api_token = "your_api_token_here"  # 必须设置有效的API Token
default_voice = "原神-中文-派蒙_ZH"  # 默认音色
timeout = 60  # 请求超时时间（秒）

# TTS模型和格式
model = "tts-v4"        # TTS模型版本
response_format = "mp3"  # 音频输出格式
speed = 1.0             # 语音播放速度

# 语言设置
text_lang = "中英混合"    # 文本语言类型
prompt_lang = "中文"      # 提示语言
emotion = "默认"          # 情感表达

# 采样参数
top_k = 10               # Top-K采样参数
top_p = 1.0              # Top-P采样参数
temperature = 1.0        # 温度参数
repetition_penalty = 1.35 # 重复惩罚系数
sample_steps = 16        # 采样步数
seed = -1               # 随机种子

# 文本处理
text_split_method = "凑四句一切"  # 文本分割方法
batch_size = 1           # 批处理大小
batch_threshold = 0.75   # 批处理阈值

# 推理设置
split_bucket = true      # 是否启用分桶处理
fragment_interval = 0.3  # 音频片段间隔
parallel_infer = true    # 是否启用并行推理
if_sr = false           # 是否启用超分辨率
```

## 故障排除

### 常见问题

1. **API Token错误**
   - 确保在配置文件中正确设置了 `api_token`
   - 检查Token是否有效且未过期

2. **网络连接问题**
   - 检查网络连接是否正常
   - 确认API地址是否可访问
   - 适当增加 `timeout` 值

3. **音频文件生成失败**
   - 检查文本内容是否合法
   - 确认音色参数是否正确
   - 查看日志获取详细错误信息

### 日志查看

插件会输出详细的日志信息，可以通过日志查看具体的错误原因：

```
[gsv2p_tts_plugin] 开始GSV2P语音合成，文本：你好世界...
[gsv2p_tts_plugin] 调用GSV2P API: https://gsv2p.acgnai.top/v1/audio/speech
[gsv2p_tts_plugin] GSV2P音频文件生成成功: /tmp/gsv2p_tts_12345678.mp3
```

## 版本信息

- **版本**：1.0.0
- **作者**：靓仔
- **依赖**：aiohttp

## 致谢

感谢以下开发者和贡献者为GSV2P项目做出的贡献：

- **GPT-SoVITS开发者**：@花儿不哭
- **模型训练者**：@红血球AE3803 @白菜工厂1145号员工
- **推理特化包适配 & 在线推理**：@AI-Hobbyist

## 许可证

本插件遵循相应的开源许可证。
