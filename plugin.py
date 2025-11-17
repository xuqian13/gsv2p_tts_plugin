"""
GSV2P TTS 插件 - 文本转语音

基于 GSV2P API 的语音合成插件，将文本转换为语音并发送。
API: https://gsv2p.acgnai.top
"""

from typing import List, Tuple, Type, Optional
import aiohttp
import asyncio
import os
import json
from src.common.logger import get_logger
from src.plugin_system.base.base_plugin import BasePlugin
from src.plugin_system.apis.plugin_register_api import register_plugin
from src.plugin_system.base.base_action import BaseAction, ActionActivationType
from src.plugin_system.base.base_command import BaseCommand
from src.plugin_system.base.component_types import ComponentInfo, ChatMode
from src.plugin_system.base.config_types import ConfigField

logger = get_logger("gsv2p_tts_plugin")


class GSV2PTTSAction(BaseAction):
    """自动触发的语音合成 Action"""

    action_name = "gsv2p_tts_action"
    action_description = "使用GSV2P模型将文本转换为语音并发送"

    activation_type = ActionActivationType.KEYWORD
    mode_enable = ChatMode.ALL
    parallel_action = False

    activation_keywords = ["语音", "说话", "朗读", "念出来", "用语音说", "gsv2p", "tts"]
    keyword_case_sensitive = False

    action_parameters = {
        "text": "要转换为语音的文本内容",
    }
    action_require = [
        "当用户要求用语音回复时使用",
        "当用户说'用语音说'、'念出来'等时使用",
        "当需要语音播报重要信息时使用"
    ]
    associated_types = ["text"]

    async def execute(self) -> Tuple[bool, str]:
        """执行语音合成"""
        try:
            text = self.action_data.get("text", "").strip()
            voice = self.action_data.get("voice", "")

            if not text:
                await self.send_text("❌ 请提供要转换为语音的文本内容")
                return False, "缺少文本内容"

            # 读取配置
            api_url = self.get_config("gsv2p.api_url", "https://gsv2p.acgnai.top/v1/audio/speech")
            api_token = self.get_config("gsv2p.api_token", "")
            default_voice = self.get_config("gsv2p.default_voice", "")
            timeout = self.get_config("gsv2p.timeout", 30)

            if not api_token:
                await self.send_text("❌ 请在配置文件中设置API Token")
                return False, "缺少API Token"

            if not voice:
                voice = default_voice

            if not voice:
                await self.send_text("❌ 请在配置文件中设置默认音色")
                return False, "缺少音色参数"

            logger.info(f"{self.log_prefix} 开始语音合成: {text[:50]}..., 音色: {voice}")

            # 调用 API 生成语音
            audio_path = await self._call_gsv2p_api(api_url, api_token, text, voice, timeout)

            if audio_path:
                await self.send_custom(message_type="voiceurl", content=audio_path)
                logger.info(f"{self.log_prefix} 语音发送成功")
                return True, f"成功生成并发送语音"
            else:
                await self.send_text("❌ 语音合成失败，请稍后重试")
                return False, "语音合成失败"

        except Exception as e:
            logger.error(f"{self.log_prefix} 语音合成出错: {e}")
            await self.send_text(f"❌ 语音合成出错: {e}")
            return False, f"语音合成出错: {e}"

    async def _call_gsv2p_api(self, api_url: str, api_token: str, text: str, voice: str, timeout: int) -> Optional[str]:
        """调用 GSV2P API 生成语音文件"""
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

            # 发送 API 请求
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.post(api_url, json=request_data, headers=headers) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        audio_data = await response.read()

                        # 检查是否是错误的 JSON 响应
                        if 'application/json' in content_type:
                            try:
                                error_json = json.loads(audio_data.decode('utf-8'))
                                logger.error(f"API返回错误: {error_json}")
                                return None
                            except:
                                pass

                        # 检查音频数据有效性
                        if len(audio_data) < 100:
                            logger.error(f"音频数据过小: {len(audio_data)} 字节")
                            return None

                        # 保存音频文件到项目根目录
                        audio_path = os.path.abspath("gsv2p_tts_output.mp3")
                        with open(audio_path, "wb") as f:
                            f.write(audio_data)

                        logger.info(f"音频文件生成成功: {audio_path} ({len(audio_data)} 字节)")
                        return audio_path
                    else:
                        error_text = await response.text()
                        logger.error(f"API调用失败: {response.status} - {error_text}")
                        return None

        except asyncio.TimeoutError:
            logger.error("API调用超时")
            return None
        except Exception as e:
            logger.error(f"API调用出错: {e}")
            return None


class GSV2PTTSCommand(BaseCommand):
    """手动触发的语音合成 Command"""

    command_name = "gsv2p_tts_command"
    command_description = "使用GSV2P模型将文本转换为语音"

    command_pattern = r"^/gsv2p\s+(?P<text>.+?)(?:\s+(?P<voice>\S+))?$"
    command_help = "使用GSV2P将文本转换为语音。用法：/gsv2p 你好世界 [音色]"
    command_examples = [
        "/gsv2p 你好，世界！",
        "/gsv2p 今天天气不错 原神-中文-派蒙_ZH",
        "/gsv2p こんにちは"
    ]
    intercept_message = True

    async def execute(self) -> Tuple[bool, str]:
        """执行语音合成命令"""
        try:
            text = self.matched_groups.get("text", "").strip()
            voice = self.matched_groups.get("voice", "")

            if not text:
                await self.send_text("❌ 请输入要转换为语音的文本内容")
                return False, "缺少文本内容"

            # 读取配置
            api_url = self.get_config("gsv2p.api_url", "https://gsv2p.acgnai.top/v1/audio/speech")
            api_token = self.get_config("gsv2p.api_token", "")
            default_voice = self.get_config("gsv2p.default_voice", "")
            timeout = self.get_config("gsv2p.timeout", 30)

            if not api_token:
                await self.send_text("❌ 请在配置文件中设置API Token")
                return False, "缺少API Token"

            if not voice:
                voice = default_voice

            if not voice:
                await self.send_text("❌ 请在配置文件中设置默认音色")
                return False, "缺少音色参数"

            logger.info(f"执行语音合成命令: {text[:50]}..., 音色: {voice}")

            # 调用 API 生成语音
            audio_path = await self._call_gsv2p_api(api_url, api_token, text, voice, timeout)

            if audio_path:
                await self.send_type(message_type="voiceurl", content=audio_path)
                return True, f"成功生成并发送语音"
            else:
                await self.send_text("❌ 语音合成失败，请稍后重试")
                return False, "语音合成失败"

        except Exception as e:
            logger.error(f"命令执行出错: {e}")
            await self.send_text(f"❌ 语音合成出错: {e}")
            return False, f"语音合成出错: {e}"

    async def _call_gsv2p_api(self, api_url: str, api_token: str, text: str, voice: str, timeout: int) -> Optional[str]:
        """调用 GSV2P API 生成语音文件"""
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

            # 发送 API 请求
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.post(api_url, json=request_data, headers=headers) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        audio_data = await response.read()

                        # 检查是否是错误的 JSON 响应
                        if 'application/json' in content_type:
                            try:
                                error_json = json.loads(audio_data.decode('utf-8'))
                                logger.error(f"API返回错误: {error_json}")
                                return None
                            except:
                                pass

                        # 检查音频数据有效性
                        if len(audio_data) < 100:
                            logger.error(f"音频数据过小: {len(audio_data)} 字节")
                            return None

                        # 保存音频文件到项目根目录
                        audio_path = os.path.abspath("gsv2p_tts_output.mp3")
                        with open(audio_path, "wb") as f:
                            f.write(audio_data)

                        logger.info(f"音频文件生成成功: {audio_path} ({len(audio_data)} 字节)")
                        return audio_path
                    else:
                        error_text = await response.text()
                        logger.error(f"API调用失败: {response.status} - {error_text}")
                        return None

        except asyncio.TimeoutError:
            logger.error("API调用超时")
            return None
        except Exception as e:
            logger.error(f"API调用出错: {e}")
            return None


@register_plugin
class GSV2PTTSPlugin(BasePlugin):
    """GSV2P TTS 插件"""

    plugin_name = "gsv2p_tts_plugin"
    plugin_description = "基于GSV2P API的文本转语音插件，支持多种语言和音色"
    plugin_version = "1.0.0"
    plugin_author = "Augment Agent"
    enable_plugin = True
    config_file_name = "config.toml"
    dependencies = []
    python_dependencies = ["aiohttp"]

    config_section_descriptions = {
        "plugin": "插件基本配置",
        "components": "组件启用控制",
        "gsv2p": "GSV2P API配置"
    }

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
        """返回插件组件列表"""
        components = []

        try:
            action_enabled = self.get_config("components.action_enabled", True)
            command_enabled = self.get_config("components.command_enabled", True)
        except AttributeError:
            action_enabled = True
            command_enabled = True

        if action_enabled:
            components.append((GSV2PTTSAction.get_action_info(), GSV2PTTSAction))

        if command_enabled:
            components.append((GSV2PTTSCommand.get_command_info(), GSV2PTTSCommand))

        return components
