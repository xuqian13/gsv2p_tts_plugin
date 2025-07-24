"""
GSV2P TTS 插件

基于 GSV2P API 的文本转语音插件，支持多种语言和高级语音合成参数。

功能特性：
- 支持中文、英文、中英混合等多种语言
- 丰富的语音合成参数配置
- 多种音色选择
- Action自动触发和Command手动触发两种模式
- 支持配置文件自定义设置

使用方法：
- Action触发：发送包含"语音"、"说话"等关键词的消息
- Command触发：/gsv2p 你好世界 [音色]

API接口：https://gsv2p.acgnai.top/v1/audio/speech

致谢：
- GPT-SoVITS开发者：@花儿不哭
- 模型训练者：@红血球AE3803 @白菜工厂1145号员工
- 推理特化包适配 & 在线推理：@AI-Hobbyist
"""

from typing import List, Tuple, Type, Optional
import aiohttp
import asyncio
import tempfile
import uuid
import json
from src.common.logger import get_logger
from src.plugin_system.base.base_plugin import BasePlugin
from src.plugin_system.apis.plugin_register_api import register_plugin
from src.plugin_system.base.base_action import BaseAction, ActionActivationType, ChatMode
from src.plugin_system.base.base_command import BaseCommand
from src.plugin_system.base.component_types import ComponentInfo
from src.plugin_system.base.config_types import ConfigField

logger = get_logger("gsv2p_tts_plugin")

# ===== Action组件 =====
class GSV2PTTSAction(BaseAction):
    """GSV2P TTS Action - 智能语音合成"""
    
    action_name = "gsv2p_tts_action"
    action_description = "使用GSV2P模型将文本转换为语音并发送"
    
    # 激活设置
    focus_activation_type = ActionActivationType.KEYWORD
    normal_activation_type = ActionActivationType.KEYWORD
    mode_enable = ChatMode.ALL
    parallel_action = False
    
    # 关键词激活
    activation_keywords = ["语音", "说话", "朗读", "念出来", "用语音说", "gsv2p", "tts"]
    keyword_case_sensitive = False
    
    # Action参数
    action_parameters = {
        "text": "要转换为语音的文本内容",
        #"voice": "音色名称，可选"
    }
    action_require = [
        "当用户要求用语音回复时使用",
        "当用户说'用语音说'、'念出来'等时使用",
        "当需要语音播报重要信息时使用"
    ]
    associated_types = ["text"]
    
    async def execute(self) -> Tuple[bool, str]:
        """执行GSV2P TTS语音合成"""
        try:
            # 获取参数
            text = self.action_data.get("text", "").strip()
            voice = self.action_data.get("voice", "")
            
            if not text:
                await self.send_text("❌ 请提供要转换为语音的文本内容")
                return False, "缺少文本内容"
            
            # 从配置获取设置
            api_url = self.get_config("gsv2p.api_url", "https://gsv2p.acgnai.top/v1/audio/speech")
            api_token = self.get_config("gsv2p.api_token", "")
            default_voice = self.get_config("gsv2p.default_voice", "")
            timeout = self.get_config("gsv2p.timeout", 30)
            
            if not api_token:
                await self.send_text("❌ 请在配置文件中设置API Token")
                return False, "缺少API Token"
            
            # 使用默认音色如果未指定
            if not voice:
                voice = default_voice

            # 检查音色是否仍为空
            if not voice:
                await self.send_text("❌ 请在配置文件中设置默认音色或在命令中指定音色")
                return False, "缺少音色参数"

            logger.info(f"{self.log_prefix} 开始GSV2P语音合成，文本：{text[:50]}..., 音色：{voice}")

            # 调用GSV2P API
            audio_path = await self._call_gsv2p_api(api_url, api_token, text, voice, timeout)
            
            if audio_path:
                # 发送语音文件
                await self.send_custom(message_type="voiceurl", content=audio_path)
                logger.info(f"{self.log_prefix} GSV2P语音发送成功")
                return True, f"成功生成并发送语音：{text[:30]}..."
            else:
                await self.send_text("❌ 语音合成失败，请稍后重试")
                return False, "语音合成失败"
                
        except Exception as e:
            logger.error(f"{self.log_prefix} GSV2P语音合成出错: {e}")
            await self.send_text(f"❌ 语音合成出错: {e}")
            return False, f"语音合成出错: {e}"
    
    async def _call_gsv2p_api(self, api_url: str, api_token: str, text: str, voice: str, timeout: int) -> Optional[str]:
        """调用GSV2P API生成语音"""
        try:
            # 构建请求数据
            request_data = {
                "model": self.get_config("gsv2p.model", "tts-v4"),
                "input": text,
                "voice": voice,
                "response_format": self.get_config("gsv2p.response_format", "mp3"),
                "speed": self.get_config("gsv2p.speed", 1),
                "other_params": {
                    "text_lang": self.get_config("gsv2p.text_lang", "中英混合"),
                    "prompt_lang": self.get_config("gsv2p.prompt_lang", "中文"),
                    "emotion": self.get_config("gsv2p.emotion", "默认"),
                    "top_k": self.get_config("gsv2p.top_k", 10),
                    "top_p": self.get_config("gsv2p.top_p", 1),
                    "temperature": self.get_config("gsv2p.temperature", 1),
                    "text_split_method": self.get_config("gsv2p.text_split_method", "按标点符号切"),
                    "batch_size": self.get_config("gsv2p.batch_size", 1),
                    "batch_threshold": self.get_config("gsv2p.batch_threshold", 0.75),
                    "split_bucket": self.get_config("gsv2p.split_bucket", True),
                    "fragment_interval": self.get_config("gsv2p.fragment_interval", 0.3),
                    "parallel_infer": self.get_config("gsv2p.parallel_infer", True),
                    "repetition_penalty": self.get_config("gsv2p.repetition_penalty", 1.35),
                    "sample_steps": self.get_config("gsv2p.sample_steps", 16),
                    "if_sr": self.get_config("gsv2p.if_sr", False),
                    "seed": self.get_config("gsv2p.seed", -1)
                }
            }
            logger.info(f"请求数据: {request_data}")
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"调用GSV2P API: {api_url}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.post(api_url, json=request_data, headers=headers) as response:
                    logger.info(f"GSV2P API响应状态: {response.status}")
                    logger.info(f"GSV2P API响应头: {dict(response.headers)}")

                    if response.status == 200:
                        # 检查响应内容类型
                        content_type = response.headers.get('content-type', '').lower()
                        logger.info(f"响应内容类型: {content_type}")

                        # 读取响应数据
                        audio_data = await response.read()
                        logger.info(f"接收到数据大小: {len(audio_data)} 字节")

                        # 检查是否是JSON错误响应
                        if 'application/json' in content_type:
                            try:
                                error_json = json.loads(audio_data.decode('utf-8'))
                                logger.error(f"API返回错误JSON: {error_json}")
                                return None
                            except:
                                pass

                        # 检查数据是否为空或过小
                        if len(audio_data) < 100:  # 音频文件应该至少有100字节
                            logger.error(f"音频数据过小，可能损坏: {len(audio_data)} 字节")
                            logger.error(f"数据内容: {audio_data[:50]}")
                            return None

                        # 保存音频文件
                        filename = f"gsv2p_tts.mp3"
                        temp_path = tempfile.gettempdir()
                        audio_path = f"{temp_path}/{filename}"

                        with open(audio_path, "wb") as f:
                            f.write(audio_data)

                        logger.info(f"GSV2P音频文件生成成功: {audio_path}")
                        logger.info(f"文件大小: {len(audio_data)} 字节")
                        return audio_path
                    else:
                        error_text = await response.text()
                        logger.error(f"GSV2P API调用失败: {response.status} - {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("GSV2P API调用超时")
            return None
        except Exception as e:
            logger.error(f"GSV2P API调用出错: {e}")
            return None

# ===== Command组件 =====
class GSV2PTTSCommand(BaseCommand):
    """GSV2P TTS Command - 手动语音合成命令"""
    
    command_name = "gsv2p_tts_command"
    command_description = "使用GSV2P模型将文本转换为语音"
    
    # 命令匹配模式：/gsv2p 文本内容 [音色]
    command_pattern = r"^/gsv2p\s+(?P<text>.+?)(?:\s+(?P<voice>\S+))?$"
    command_help = "使用GSV2P将文本转换为语音。用法：/gsv2p 你好世界 [音色]"
    command_examples = [
        "/gsv2p 你好，世界！",
        "/gsv2p 今天天气不错 voice1",
        "/gsv2p こんにちは voice2"
    ]
    intercept_message = True
    
    async def execute(self) -> Tuple[bool, str]:
        """执行GSV2P TTS命令"""
        try:
            # 获取匹配的参数
            text = self.matched_groups.get("text", "").strip()
            voice = self.matched_groups.get("voice", "")
            
            if not text:
                await self.send_text("❌ 请输入要转换为语音的文本内容")
                return False, "缺少文本内容"
            
            # 从配置获取设置
            api_url = self.get_config("gsv2p.api_url", "https://gsv2p.acgnai.top/v1/audio/speech")
            api_token = self.get_config("gsv2p.api_token", "")
            default_voice = self.get_config("gsv2p.default_voice", "")
            timeout = self.get_config("gsv2p.timeout", 30)
            
            if not api_token:
                await self.send_text("❌ 请在配置文件中设置API Token")
                return False, "缺少API Token"
            
            # 使用默认音色如果未指定
            if not voice:
                voice = default_voice

            # 检查音色是否仍为空
            if not voice:
                await self.send_text("❌ 请在配置文件中设置默认音色或在命令中指定音色")
                return False, "缺少音色参数"

            logger.info(f"执行GSV2P命令，文本：{text[:50]}..., 音色：{voice}")

            # 调用GSV2P API
            audio_path = await self._call_gsv2p_api(api_url, api_token, text, voice, timeout)
            
            if audio_path:
                # 发送语音文件
                await self.send_type(message_type="voiceurl", content=audio_path)
                return True, f"成功生成并发送语音：{text[:30]}..."
            else:
                await self.send_text("❌ 语音合成失败，请稍后重试")
                return False, "语音合成失败"
                
        except Exception as e:
            logger.error(f"GSV2P命令执行出错: {e}")
            await self.send_text(f"❌ 语音合成出错: {e}")
            return False, f"语音合成出错: {e}"
    
    async def _call_gsv2p_api(self, api_url: str, api_token: str, text: str, voice: str, timeout: int) -> Optional[str]:
        """调用GSV2P API生成语音"""
        try:
            # 构建请求数据
            request_data = {
                "model": self.get_config("gsv2p.model", "tts-v4"),
                "input": text,
                "voice": voice,
                "response_format": self.get_config("gsv2p.response_format", "mp3"),
                "speed": self.get_config("gsv2p.speed", 1),
                "other_params": {
                    "text_lang": self.get_config("gsv2p.text_lang", "中英混合"),
                    "prompt_lang": self.get_config("gsv2p.prompt_lang", "中文"),
                    "emotion": self.get_config("gsv2p.emotion", "默认"),
                    "top_k": self.get_config("gsv2p.top_k", 10),
                    "top_p": self.get_config("gsv2p.top_p", 1),
                    "temperature": self.get_config("gsv2p.temperature", 1),
                    "text_split_method": self.get_config("gsv2p.text_split_method", "按标点符号切"),
                    "batch_size": self.get_config("gsv2p.batch_size", 1),
                    "batch_threshold": self.get_config("gsv2p.batch_threshold", 0.75),
                    "split_bucket": self.get_config("gsv2p.split_bucket", True),
                    "fragment_interval": self.get_config("gsv2p.fragment_interval", 0.3),
                    "parallel_infer": self.get_config("gsv2p.parallel_infer", True),
                    "repetition_penalty": self.get_config("gsv2p.repetition_penalty", 1.35),
                    "sample_steps": self.get_config("gsv2p.sample_steps", 16),
                    "if_sr": self.get_config("gsv2p.if_sr", False),
                    "seed": self.get_config("gsv2p.seed", -1)
                }
            }
            
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"调用GSV2P API: {api_url}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.post(api_url, json=request_data, headers=headers) as response:
                    logger.info(f"GSV2P API响应状态: {response.status}")
                    logger.info(f"GSV2P API响应头: {dict(response.headers)}")

                    if response.status == 200:
                        # 检查响应内容类型
                        content_type = response.headers.get('content-type', '').lower()
                        logger.info(f"响应内容类型: {content_type}")

                        # 读取响应数据
                        audio_data = await response.read()
                        logger.info(f"接收到数据大小: {len(audio_data)} 字节")

                        # 检查是否是JSON错误响应
                        if 'application/json' in content_type:
                            try:
                                error_json = json.loads(audio_data.decode('utf-8'))
                                logger.error(f"API返回错误JSON: {error_json}")
                                return None
                            except:
                                pass

                        # 检查数据是否为空或过小
                        if len(audio_data) < 100:  # 音频文件应该至少有100字节
                            logger.error(f"音频数据过小，可能损坏: {len(audio_data)} 字节")
                            logger.error(f"数据内容: {audio_data[:50]}")
                            return None

                        # 保存音频文件
                        filename = f"gsv2p_tts_{uuid.uuid4().hex[:8]}.mp3"
                        temp_path = tempfile.gettempdir()
                        audio_path = f"{temp_path}/{filename}"

                        with open(audio_path, "wb") as f:
                            f.write(audio_data)

                        logger.info(f"GSV2P音频文件生成成功: {audio_path}")
                        logger.info(f"文件大小: {len(audio_data)} 字节")
                        return audio_path
                    else:
                        error_text = await response.text()
                        logger.error(f"GSV2P API调用失败: {response.status} - {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("GSV2P API调用超时")
            return None
        except Exception as e:
            logger.error(f"GSV2P API调用出错: {e}")
            return None
    
# ===== 插件注册 =====
@register_plugin
class GSV2PTTSPlugin(BasePlugin):
    """GSV2P TTS插件 - 基于GSV2P API的文本转语音插件"""

    plugin_name = "gsv2p_tts_plugin"
    plugin_description = "基于GSV2P API的文本转语音插件，支持多种语言和高级语音合成参数"
    plugin_version = "1.0.0"
    plugin_author = "Augment Agent"
    enable_plugin = True
    config_file_name = "config.toml"
    dependencies = []  # 插件依赖列表
    python_dependencies = ["aiohttp"]  # Python包依赖列表

    # 配置节描述
    config_section_descriptions = {
        "plugin": "插件基本配置",
        "components": "组件启用控制",
        "gsv2p": "GSV2P API配置"
    }

    # 配置Schema定义
    config_schema = {
        "plugin": {
            "enabled": ConfigField(type=bool, default=True, description="是否启用插件")
        },
        "components": {
            "action_enabled": ConfigField(type=bool, default=True, description="是否启用Action组件"),
            "command_enabled": ConfigField(type=bool, default=True, description="是否启用Command组件")
        },
        "gsv2p": {
            "api_url": ConfigField(
                type=str,
                default="https://gsv2p.acgnai.top/v1/audio/speech",
                description="GSV2P API地址"
            ),
            "api_token": ConfigField(type=str, default="", description="API认证Token"),
            "default_voice": ConfigField(type=str, default="原神-中文-派蒙_ZH", description="默认音色"),
            "timeout": ConfigField(type=int, default=30, description="API请求超时时间（秒）"),
            "model": ConfigField(type=str, default="tts-v4", description="TTS模型"),
            "response_format": ConfigField(type=str, default="mp3", description="音频格式"),
            "speed": ConfigField(type=float, default=1.0, description="语音速度"),
            "text_lang": ConfigField(type=str, default="中英混合", description="文本语言"),
            "prompt_lang": ConfigField(type=str, default="中文", description="提示语言"),
            "emotion": ConfigField(type=str, default="默认", description="情感"),
            "top_k": ConfigField(type=int, default=10, description="Top-K采样"),
            "top_p": ConfigField(type=float, default=1.0, description="Top-P采样"),
            "temperature": ConfigField(type=float, default=1.0, description="温度参数"),
            "text_split_method": ConfigField(type=str, default="按标点符号切", description="文本分割方法"),
            "batch_size": ConfigField(type=int, default=1, description="批处理大小"),
            "batch_threshold": ConfigField(type=float, default=0.75, description="批处理阈值"),
            "split_bucket": ConfigField(type=bool, default=True, description="是否分桶"),
            "fragment_interval": ConfigField(type=float, default=0.3, description="片段间隔"),
            "parallel_infer": ConfigField(type=bool, default=True, description="是否并行推理"),
            "repetition_penalty": ConfigField(type=float, default=1.35, description="重复惩罚"),
            "sample_steps": ConfigField(type=int, default=16, description="采样步数"),
            "if_sr": ConfigField(type=bool, default=False, description="是否超分辨率"),
            "seed": ConfigField(type=int, default=-1, description="随机种子")
        }
    }

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        """返回插件包含的组件列表"""
        components = []

        # 根据配置决定是否启用组件（如果get_config方法不可用，则默认启用）
        try:
            action_enabled = self.get_config("components.action_enabled", True)
            command_enabled = self.get_config("components.command_enabled", True)
        except AttributeError:
            # 如果get_config方法不存在，默认启用所有组件
            action_enabled = True
            command_enabled = True

        if action_enabled:
            components.append((GSV2PTTSAction.get_action_info(), GSV2PTTSAction))

        if command_enabled:
            components.append((GSV2PTTSCommand.get_command_info(), GSV2PTTSCommand))

        return components
