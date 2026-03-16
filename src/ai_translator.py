"""
AI-based translation service supporting OpenAI, Ollama, custom API providers, and offline translation.
"""
import os
import json
import logging
import subprocess
import sys
import requests

try:
    import torch
    torch.set_num_threads(4)
except:
    pass
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

OLLAMA_DEFAULT_URL = "http://localhost:11434"
OPENAI_DEFAULT_URL = "https://api.openai.com/v1"

HF_ENDPOINT = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com")

OFFLINE_TRANSLATOR_AVAILABLE = False
OFFLINE_BACKEND = None

try:
    import argostranslate.translate
    import argostranslate.package
    OFFLINE_TRANSLATOR_AVAILABLE = True
    OFFLINE_BACKEND = "argostranslate"
    logger.debug("argostranslate available for offline translation")
except Exception as e:
    logger.debug("argostranslate not available: %s", e)

if not OFFLINE_TRANSLATOR_AVAILABLE:
    try:
        from translatepy import Translator as TranslatepyTranslator
        OFFLINE_TRANSLATOR_AVAILABLE = True
        OFFLINE_BACKEND = "translatepy"
        logger.debug("translatepy available for offline translation")
    except Exception as e:
        logger.debug("translatepy not available: %s", e)

if not OFFLINE_TRANSLATOR_AVAILABLE:
    try:
        from transformers import MarianMTModel, MarianTokenizer
        OFFLINE_TRANSLATOR_AVAILABLE = True
        OFFLINE_BACKEND = "transformers"
        logger.debug("HuggingFace transformers available for offline translation")
    except Exception as e:
        logger.debug("transformers not available: %s", e)

if not OFFLINE_TRANSLATOR_AVAILABLE:
    OFFLINE_TRANSLATOR_AVAILABLE = True
    OFFLINE_BACKEND = "builtin"
    logger.debug("Using built-in dictionary translator (limited quality)")


def install_offline_translator() -> bool:
    """Install offline translation package."""
    global OFFLINE_TRANSLATOR_AVAILABLE, OFFLINE_BACKEND
    
    if OFFLINE_TRANSLATOR_AVAILABLE:
        return True
    
    env = dict(subprocess.os.environ)
    env["CURL_CA_BUNDLE"] = ""
    env["REQUESTS_CA_BUNDLE"] = ""
    env["SSL_CERT_FILE"] = ""
    env["PIP_CERT"] = ""
    
    packages_to_try = [
        ("translatepy", "translatepy"),
        ("argostranslate", "argostranslate")
    ]
    
    for pkg_name, import_name in packages_to_try:
        logger.info("Installing %s for offline translation...", pkg_name)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg_name,
                 "--trusted-host", "pypi.org",
                 "--trusted-host", "files.pythonhosted.org",
                 "--trusted-host", "pypi.python.org",
                 "--trusted-host", "upload.pypi.org"],
                capture_output=True,
                text=True,
                timeout=300,
                env=env
            )
            
            if result.returncode == 0:
                if pkg_name == "translatepy":
                    from translatepy import Translator as TranslatepyTranslator
                    OFFLINE_TRANSLATOR_AVAILABLE = True
                    OFFLINE_BACKEND = "translatepy"
                    logger.info("translatepy installed successfully")
                    return True
                elif pkg_name == "argostranslate":
                    import argostranslate.translate
                    import argostranslate.package
                    OFFLINE_TRANSLATOR_AVAILABLE = True
                    OFFLINE_BACKEND = "argostranslate"
                    logger.info("argostranslate installed successfully")
                    return True
            else:
                logger.warning("Failed to install %s: %s", pkg_name, result.stderr)
        except Exception as e:
            logger.warning("Error installing %s: %s", pkg_name, e)
    
    return False


@dataclass
class AIProvider:
    """Configuration for an AI provider."""
    name: str
    provider_type: str  # openai, ollama, custom
    api_url: str
    api_key: str
    model: str
    model_type: str  # chat, completion
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "provider_type": self.provider_type,
            "api_url": self.api_url,
            "api_key": self.api_key,
            "model": self.model,
            "model_type": self.model_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIProvider':
        return cls(
            name=data.get("name", "Unknown"),
            provider_type=data.get("provider_type", "custom"),
            api_url=data.get("api_url", ""),
            api_key=data.get("api_key", ""),
            model=data.get("model", ""),
            model_type=data.get("model_type", "chat")
        )


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: str = OLLAMA_DEFAULT_URL):
        self.base_url = base_url.rstrip('/')
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models from Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = []
                for model in data.get("models", []):
                    models.append({
                        "name": model.get("name", ""),
                        "size": model.get("size", 0),
                        "modified_at": model.get("modified_at", ""),
                        "details": model.get("details", {})
                    })
                logger.info("Found %d Ollama models", len(models))
                return models
            else:
                logger.warning("Ollama returned status %d", response.status_code)
                return []
        except requests.exceptions.ConnectionError:
            logger.warning("Ollama not running at %s", self.base_url)
            return []
        except requests.exceptions.Timeout:
            logger.warning("Ollama request timed out")
            return []
        except Exception as e:
            logger.error("Failed to list Ollama models: %s", e)
            return []
    
    def is_running(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def chat(self, model: str, messages: List[Dict[str, str]], stream: bool = False) -> Optional[str]:
        """Send a chat request to Ollama."""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream
            }
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")
            else:
                logger.error("Ollama chat error: %s", response.text)
                return None
        except Exception as e:
            logger.error("Ollama chat failed: %s", e)
            return None


class OpenAIClient:
    """Client for OpenAI-compatible APIs (OpenAI, custom endpoints)."""
    
    def __init__(self, api_url: str = OPENAI_DEFAULT_URL, api_key: str = ""):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.proxies = {'http': None, 'https': None}
    
    def chat(self, model: str, messages: List[Dict[str, str]]) -> Optional[str]:
        """Send a chat request to OpenAI-compatible API."""
        if not self.api_key:
            logger.error("API key required for OpenAI-compatible API")
            return None
        
        try:
            import os
            old_http = os.environ.get('HTTP_PROXY')
            old_https = os.environ.get('HTTPS_PROXY')
            old_all = os.environ.get('ALL_PROXY')
            os.environ['HTTP_PROXY'] = ''
            os.environ['HTTPS_PROXY'] = ''
            os.environ['ALL_PROXY'] = ''
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.3
            }
            logger.debug("Sending request to %s/chat/completions with model %s", self.api_url, model)
            response = self.session.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if old_http: os.environ['HTTP_PROXY'] = old_http
            if old_https: os.environ['HTTPS_PROXY'] = old_https
            if old_all: os.environ['ALL_PROXY'] = old_all
            
            logger.debug("API response status: %d", response.status_code)
            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    logger.debug("API response content: %s", content[:200] if content else "empty")
                    return content
                return None
            else:
                logger.error("OpenAI API error: %s", response.text)
                return None
        except Exception as e:
            logger.error("OpenAI chat failed: %s", e)
            return None
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models from OpenAI-compatible API."""
        if not self.api_key:
            return []
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            response = self.session.get(
                f"{self.api_url}/models",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                models = []
                for model in data.get("data", []):
                    models.append({
                        "name": model.get("id", ""),
                        "owned_by": model.get("owned_by", "")
                    })
                return models
            return []
        except Exception as e:
            logger.error("Failed to list OpenAI models: %s", e)
            return []


SIMPLE_DICTIONARY = {
    "en->zh": {
        "hello": "你好",
        "world": "世界",
        "good": "好",
        "bad": "坏",
        "yes": "是",
        "no": "不",
        "thank": "谢谢",
        "please": "请",
        "sorry": "对不起",
        "help": "帮助",
        "love": "爱",
        "happy": "快乐",
        "sad": "悲伤",
        "big": "大",
        "small": "小",
        "new": "新",
        "old": "旧",
        "goodbye": "再见",
        "morning": "早上",
        "night": "晚上",
        "day": "天",
        "time": "时间",
        "people": "人们",
        "person": "人",
        "friend": "朋友",
        "family": "家庭",
        "water": "水",
        "food": "食物",
        "house": "房子",
        "car": "汽车",
        "book": "书",
        "computer": "电脑",
        "phone": "电话",
        "work": "工作",
        "school": "学校",
        "home": "家",
        "today": "今天",
        "tomorrow": "明天",
        "yesterday": "昨天",
        "now": "现在",
        "later": "以后",
        "always": "总是",
        "never": "从不",
        "maybe": "也许",
        "monday": "星期一",
        "tuesday": "星期二",
        "wednesday": "星期三",
        "thursday": "星期四",
        "friday": "星期五",
        "saturday": "星期六",
        "sunday": "星期日",
        "january": "一月",
        "february": "二月",
        "march": "三月",
        "april": "四月",
        "may": "五月",
        "june": "六月",
        "july": "七月",
        "august": "八月",
        "september": "九月",
        "october": "十月",
        "november": "十一月",
        "december": "十二月",
        "think": "想",
        "know": "知道",
        "understand": "理解",
        "speak": "说",
        "read": "读",
        "write": "写",
        "listen": "听",
        "see": "看",
        "want": "想要",
        "need": "需要",
        "like": "喜欢",
        "hate": "讨厌",
        "open": "打开",
        "close": "关闭",
        "start": "开始",
        "stop": "停止",
        "go": "去",
        "come": "来",
        "eat": "吃",
        "drink": "喝",
        "sleep": "睡觉",
        "run": "跑",
        "walk": "走",
        "play": "玩",
        "study": "学习",
        "teach": "教",
        "learn": "学习",
        "buy": "买",
        "sell": "卖",
        "give": "给",
        "take": "拿",
        "make": "做",
        "use": "使用",
        "find": "找到",
        "look": "看",
        "feel": "感觉",
        "try": "尝试",
        "ask": "问",
        "answer": "回答",
        "call": "叫",
        "name": "名字",
        "place": "地方",
        "thing": "东西",
        "year": "年",
        "month": "月",
        "week": "周",
        "hour": "小时",
        "minute": "分钟",
        "second": "秒",
        "number": "数字",
        "money": "钱",
        "price": "价格",
        "problem": "问题",
        "question": "问题",
        "answer": "答案",
        "idea": "想法",
        "way": "方式",
        "part": "部分",
        "side": "边",
        "end": "结束",
        "beginning": "开始",
        "middle": "中间",
        "left": "左",
        "right": "右",
        "up": "上",
        "down": "下",
        "in": "在...里",
        "out": "在...外",
        "on": "在...上",
        "off": "关",
        "over": "在...上方",
        "under": "在...下方",
        "again": "再次",
        "still": "仍然",
        "already": "已经",
        "just": "只是",
        "very": "非常",
        "really": "真的",
        "quite": "相当",
        "too": "太",
        "also": "也",
        "only": "只",
        "even": "甚至",
        "here": "这里",
        "there": "那里",
        "where": "哪里",
        "when": "什么时候",
        "why": "为什么",
        "how": "怎么",
        "what": "什么",
        "who": "谁",
        "which": "哪个",
        "this": "这个",
        "that": "那个",
        "these": "这些",
        "those": "那些",
        "my": "我的",
        "your": "你的",
        "his": "他的",
        "her": "她的",
        "its": "它的",
        "our": "我们的",
        "their": "他们的",
        "me": "我",
        "you": "你",
        "he": "他",
        "she": "她",
        "it": "它",
        "we": "我们",
        "they": "他们",
        "i": "我",
        "am": "是",
        "is": "是",
        "are": "是",
        "was": "是",
        "were": "是",
        "be": "是",
        "been": "是",
        "being": "正在",
        "have": "有",
        "has": "有",
        "had": "有",
        "do": "做",
        "does": "做",
        "did": "做",
        "will": "将",
        "would": "会",
        "could": "能",
        "should": "应该",
        "can": "能",
        "may": "可能",
        "might": "可能",
        "must": "必须",
        "shall": "将",
        "the": "这",
        "a": "一个",
        "an": "一个",
        "and": "和",
        "or": "或",
        "but": "但是",
        "if": "如果",
        "because": "因为",
        "so": "所以",
        "than": "比",
        "as": "作为",
        "at": "在",
        "by": "由",
        "for": "为了",
        "from": "从",
        "to": "到",
        "with": "和",
        "without": "没有",
        "about": "关于",
        "after": "之后",
        "before": "之前",
        "between": "之间",
        "into": "进入",
        "through": "通过",
        "during": "期间",
        "while": "当",
        "of": "的",
    },
    "zh->en": {
        "你好": "hello",
        "世界": "world",
        "好": "good",
        "坏": "bad",
        "是": "yes",
        "不": "no",
        "谢谢": "thank",
        "请": "please",
        "对不起": "sorry",
        "帮助": "help",
        "爱": "love",
        "快乐": "happy",
        "悲伤": "sad",
        "大": "big",
        "小": "small",
        "新": "new",
        "旧": "old",
        "再见": "goodbye",
        "早上": "morning",
        "晚上": "night",
        "天": "day",
        "时间": "time",
        "人们": "people",
        "人": "person",
        "朋友": "friend",
        "家庭": "family",
        "水": "water",
        "食物": "food",
        "房子": "house",
        "汽车": "car",
        "书": "book",
        "电脑": "computer",
        "电话": "phone",
        "工作": "work",
        "学校": "school",
        "家": "home",
        "今天": "today",
        "明天": "tomorrow",
        "昨天": "yesterday",
        "现在": "now",
        "以后": "later",
        "总是": "always",
        "从不": "never",
        "也许": "maybe",
        "想": "think",
        "知道": "know",
        "理解": "understand",
        "说": "speak",
        "读": "read",
        "写": "write",
        "听": "listen",
        "看": "see",
        "想要": "want",
        "需要": "need",
        "喜欢": "like",
        "讨厌": "hate",
        "打开": "open",
        "关闭": "close",
        "开始": "start",
        "停止": "stop",
        "去": "go",
        "来": "come",
        "吃": "eat",
        "喝": "drink",
        "睡觉": "sleep",
        "跑": "run",
        "走": "walk",
        "玩": "play",
        "学习": "learn",
        "教": "teach",
        "买": "buy",
        "卖": "sell",
        "给": "give",
        "拿": "take",
        "做": "make",
        "使用": "use",
        "找到": "find",
        "感觉": "feel",
        "尝试": "try",
        "问": "ask",
        "回答": "answer",
        "叫": "call",
        "名字": "name",
        "地方": "place",
        "东西": "thing",
        "年": "year",
        "月": "month",
        "周": "week",
        "小时": "hour",
        "分钟": "minute",
        "秒": "second",
        "星期一": "Monday",
        "星期二": "Tuesday",
        "星期三": "Wednesday",
        "星期四": "Thursday",
        "星期五": "Friday",
        "星期六": "Saturday",
        "星期日": "Sunday",
        "一月": "January",
        "二月": "February",
        "三月": "March",
        "四月": "April",
        "五月": "May",
        "六月": "June",
        "七月": "July",
        "八月": "August",
        "九月": "September",
        "十月": "October",
        "十一月": "November",
        "十二月": "December",
        "数字": "number",
        "钱": "money",
        "价格": "price",
        "问题": "problem",
        "答案": "answer",
        "想法": "idea",
        "方式": "way",
        "部分": "part",
        "边": "side",
        "结束": "end",
        "中间": "middle",
        "左": "left",
        "右": "right",
        "上": "up",
        "下": "down",
        "在...里": "in",
        "在...外": "out",
        "在...上": "on",
        "关": "off",
        "在...上方": "over",
        "在...下方": "under",
        "再次": "again",
        "仍然": "still",
        "已经": "already",
        "只是": "just",
        "非常": "very",
        "真的": "really",
        "相当": "quite",
        "太": "too",
        "也": "also",
        "只": "only",
        "甚至": "even",
        "这里": "here",
        "那里": "there",
        "哪里": "where",
        "什么时候": "when",
        "为什么": "why",
        "怎么": "how",
        "什么": "what",
        "谁": "who",
        "哪个": "which",
        "这个": "this",
        "那个": "that",
        "这些": "these",
        "那些": "those",
        "我的": "my",
        "你的": "your",
        "他的": "his",
        "她的": "her",
        "它的": "its",
        "我们的": "our",
        "他们的": "their",
        "我": "I",
        "你": "you",
        "他": "he",
        "她": "she",
        "它": "it",
        "我们": "we",
        "他们": "they",
        "有": "have",
        "能": "can",
        "可能": "may",
        "必须": "must",
        "将": "will",
        "会": "would",
        "应该": "should",
        "和": "and",
        "或": "or",
        "但是": "but",
        "如果": "if",
        "因为": "because",
        "所以": "so",
        "比": "than",
        "作为": "as",
        "在": "at",
        "由": "by",
        "为了": "for",
        "从": "from",
        "到": "to",
        "没有": "without",
        "关于": "about",
        "之后": "after",
        "之前": "before",
        "之间": "between",
        "进入": "into",
        "通过": "through",
        "期间": "during",
        "当": "while",
        "的": "of",
    }
}


class OfflineTranslator:
    """Offline translator using argostranslate (CPU-compatible, no internet required)."""
    
    LANGUAGE_MAP = {
        "en": "English",
        "zh": "Chinese",
        "zh-CN": "Chinese",
        "zh-TW": "Chinese Traditional",
        "ja": "Japanese",
        "ko": "Korean",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "ru": "Russian",
        "pt": "Portuguese",
        "it": "Italian",
        "ar": "Arabic",
        "hi": "Hindi",
        "th": "Thai",
        "vi": "Vietnamese",
        "nl": "Dutch",
        "pl": "Polish",
        "tr": "Turkish",
        "id": "Indonesian",
        "ms": "Malay",
        "cs": "Czech",
        "sv": "Swedish",
        "da": "Danish",
        "fi": "Finnish",
        "hu": "Hungarian",
        "ro": "Romanian",
        "uk": "Ukrainian",
        "he": "Hebrew",
        "bn": "Bengali",
        "ta": "Tamil",
        "te": "Telugu",
        "ml": "Malayalam"
    }
    
    _installed_languages = None
    _translation_cache = {}
    
    def __init__(self):
        self._ensure_packages_updated()
    
    def _ensure_packages_updated(self):
        """Ensure argostranslate package index is updated."""
        if OFFLINE_TRANSLATOR_AVAILABLE:
            try:
                argostranslate.package.update_package_index()
            except Exception as e:
                logger.debug("Could not update argostranslate package index: %s", e)
    
    def _normalize_lang_code(self, lang_code: str) -> str:
        """Normalize language code for argostranslate."""
        lang_code = lang_code.lower()
        if lang_code.startswith("zh"):
            return "zh"
        return lang_code
    
    def get_installed_languages(self) -> List[Dict[str, Any]]:
        """Get list of installed language pairs for offline translation."""
        if not OFFLINE_TRANSLATOR_AVAILABLE:
            return []
        
        try:
            if self._installed_languages is None:
                self._installed_languages = argostranslate.translate.get_installed_languages()
            
            languages = []
            seen_pairs = set()
            
            for from_lang in self._installed_languages:
                for to_lang in from_lang.translations:
                    pair_key = f"{from_lang.code}->{to_lang.code}"
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        languages.append({
                            "from": from_lang.code,
                            "from_name": from_lang.name,
                            "to": to_lang.code,
                            "to_name": to_lang.name,
                            "pair": f"{from_lang.name} → {to_lang.name}"
                        })
            
            logger.info("Found %d installed offline translation pairs", len(languages))
            return languages
        except Exception as e:
            logger.error("Failed to get installed languages: %s", e)
            return []
    
    def get_available_packages(self) -> List[Dict[str, Any]]:
        """Get list of available packages that can be installed."""
        if not OFFLINE_TRANSLATOR_AVAILABLE:
            return []
        
        try:
            available_packages = argostranslate.package.get_available_packages()
            installed_codes = set()
            
            for lang in argostranslate.translate.get_installed_languages():
                installed_codes.add(lang.code)
            
            packages = []
            for pkg in available_packages:
                packages.append({
                    "from": pkg.from_code,
                    "to": pkg.to_code,
                    "from_name": pkg.from_name,
                    "to_name": pkg.to_name,
                    "installed": pkg.from_code in installed_codes and pkg.to_code in installed_codes
                })
            
            return packages
        except Exception as e:
            logger.error("Failed to get available packages: %s", e)
            return []
    
    def install_language_pair(self, from_code: str, to_code: str) -> bool:
        """Install a language pair for offline translation."""
        if not OFFLINE_TRANSLATOR_AVAILABLE:
            logger.error("argostranslate not available")
            return False
        
        try:
            available_packages = argostranslate.package.get_available_packages()
            
            package_to_install = None
            for pkg in available_packages:
                if pkg.from_code == from_code and pkg.to_code == to_code:
                    package_to_install = pkg
                    break
            
            if package_to_install:
                argostranslate.package.install_from_path(package_to_install.download())
                self._installed_languages = None
                logger.info("Installed offline translation: %s -> %s", from_code, to_code)
                return True
            else:
                logger.warning("Package not found: %s -> %s", from_code, to_code)
                return False
        except Exception as e:
            logger.error("Failed to install language pair: %s", e)
            return False
    
    def is_available(self) -> bool:
        """Check if offline translation is available."""
        return OFFLINE_TRANSLATOR_AVAILABLE
    
    def can_translate(self, source_lang: str, target_lang: str) -> bool:
        """Check if a specific translation pair is available."""
        if not OFFLINE_TRANSLATOR_AVAILABLE:
            return False
        
        try:
            source = self._normalize_lang_code(source_lang)
            target = self._normalize_lang_code(target_lang)
            
            if self._installed_languages is None:
                self._installed_languages = argostranslate.translate.get_installed_languages()
            
            for from_lang in self._installed_languages:
                if from_lang.code == source:
                    for to_lang in from_lang.translations:
                        if to_lang.code == target:
                            return True
            return False
        except Exception as e:
            logger.error("Error checking translation availability: %s", e)
            return False
    
    def _ensure_language_pair(self, source_lang: str, target_lang: str) -> bool:
        """Ensure a language pair is installed, auto-install if needed."""
        if not OFFLINE_TRANSLATOR_AVAILABLE:
            return False
        
        source = self._normalize_lang_code(source_lang)
        target = self._normalize_lang_code(target_lang)
        
        if self._installed_languages is None:
            self._installed_languages = argostranslate.translate.get_installed_languages()
        
        from_language = None
        to_language = None
        
        for lang in self._installed_languages:
            if lang.code == source:
                from_language = lang
            if lang.code == target:
                to_language = lang
        
        if from_language and to_language:
            translation = from_language.get_translation(to_language)
            if translation:
                return True
        
        logger.info("Auto-installing language pair: %s -> %s", source, target)
        try:
            available_packages = argostranslate.package.get_available_packages()
            
            for pkg in available_packages:
                if pkg.from_code == source and pkg.to_code == target:
                    argostranslate.package.install_from_path(pkg.download())
                    self._installed_languages = None
                    logger.info("Successfully installed %s -> %s", source, target)
                    return True
            
            for pkg in available_packages:
                if pkg.to_code == source and pkg.from_code == target:
                    argostranslate.package.install_from_path(pkg.download())
                    self._installed_languages = None
                    logger.info("Successfully installed %s -> %s (reverse pair)", target, source)
                    return True
            
            logger.warning("Language pair %s -> %s not found in available packages", source, target)
            return False
            
        except Exception as e:
            logger.error("Failed to auto-install language pair: %s", e)
            return False

    def translate(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Translate text using offline translation."""
        if not OFFLINE_TRANSLATOR_AVAILABLE:
            logger.error("Offline translation not available")
            return None
        
        if OFFLINE_BACKEND == "onnx":
            return self._translate_onnx(text, source_lang, target_lang)
        if OFFLINE_BACKEND == "ctranslate2":
            return self._translate_ctranslate2(text, source_lang, target_lang)
        elif OFFLINE_BACKEND == "transformers":
            return self._translate_transformers(text, source_lang, target_lang)
        elif OFFLINE_BACKEND == "translatepy":
            return self._translate_translatepy(text, source_lang, target_lang)
        elif OFFLINE_BACKEND == "argostranslate":
            return self._translate_argos(text, source_lang, target_lang)
        else:
            return self._translate_builtin(text, source_lang, target_lang)
    
    _transformer_models = {}
    
    def _translate_transformers(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Translate using HuggingFace transformers (Helsinki-NLP models)."""
        try:
            import os
            os.environ["HTTP_PROXY"] = ""
            os.environ["HTTPS_PROXY"] = ""
            os.environ["ALL_PROXY"] = ""
            os.environ["HF_ENDPOINT"] = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com")
            
            from transformers import MarianMTModel, MarianTokenizer
            import torch
            
            source = self._normalize_lang_code(source_lang)
            target = self._normalize_lang_code(target_lang)
            
            model_name = self._get_transformer_model(source, target)
            if not model_name:
                logger.warning("No transformer model for %s -> %s", source, target)
                return None
            
            cache_key = model_name
            if cache_key not in self._transformer_models:
                logger.info("Loading transformer model: %s", model_name)
                tokenizer = MarianTokenizer.from_pretrained(model_name, local_files_only=True)
                model = MarianMTModel.from_pretrained(model_name, local_files_only=True)
                model.eval()
                self._transformer_models[cache_key] = {'model': model, 'tokenizer': tokenizer}
            
            model_data = self._transformer_models[cache_key]
            model = model_data['model']
            tokenizer = model_data['tokenizer']
            
            with torch.no_grad():
                inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
                outputs = model.generate(**inputs, max_length=512, num_beams=1, do_sample=False, repetition_penalty=2.0, no_repeat_ngram_size=3)
                translated = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            if source == "en" and target == "zh":
                import re
                translated = re.sub(r'\s+', '', translated)
                translated = translated.rstrip(',，。、')
                if len(translated) > 3 and translated[-1] in '来去是早晚':
                    translated = translated[:-1]
                if len(translated) >= 4:
                    half = len(translated) // 2
                    if translated[:half] == translated[half:2*half]:
                        translated = translated[:half]
                if len(translated) > 20:
                    for i in range(2, 10):
                        pattern = translated[:i]
                        if translated.count(pattern) > 2:
                            translated = pattern
                            break
            logger.info("Transformers translated %d chars from %s to %s", len(text), source, target)
            return translated
            
            return None
            
        except Exception as e:
            logger.error("Transformers translation failed: %s", e)
            return None
    
    def _get_transformer_model(self, source: str, target: str) -> Optional[str]:
        """Get Helsinki-NLP model name for language pair."""
        source = source.lower()
        target = target.lower()
        
        if source.startswith("zh"):
            source = "zh"
        if target.startswith("zh"):
            target = "zh"
        
        models = {
            ("en", "zh"): "Helsinki-NLP/opus-mt-en-zh",
            ("zh", "en"): "Helsinki-NLP/opus-mt-zh-en",
            ("en", "ja"): "Helsinki-NLP/opus-mt-en-ja",
            ("ja", "en"): "Helsinki-NLP/opus-mt-ja-en",
            ("en", "ko"): "Helsinki-NLP/opus-mt-en-ko",
            ("ko", "en"): "Helsinki-NLP/opus-mt-ko-en",
            ("en", "es"): "Helsinki-NLP/opus-mt-en-es",
            ("es", "en"): "Helsinki-NLP/opus-mt-es-en",
            ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
            ("fr", "en"): "Helsinki-NLP/opus-mt-fr-en",
            ("en", "de"): "Helsinki-NLP/opus-mt-en-de",
            ("de", "en"): "Helsinki-NLP/opus-mt-de-en",
            ("en", "ru"): "Helsinki-NLP/opus-mt-en-ru",
            ("ru", "en"): "Helsinki-NLP/opus-mt-ru-en",
            ("en", "pt"): "Helsinki-NLP/opus-mt-en-pt",
            ("pt", "en"): "Helsinki-NLP/opus-mt-pt-en",
            ("en", "it"): "Helsinki-NLP/opus-mt-en-it",
            ("it", "en"): "Helsinki-NLP/opus-mt-it-en",
            ("en", "ar"): "Helsinki-NLP/opus-mt-en-ar",
            ("ar", "en"): "Helsinki-NLP/opus-mt-ar-en",
        }
        
        return models.get((source, target))
    
    def _translate_builtin(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Translate using built-in dictionary (basic word-by-word translation)."""
        try:
            source = self._normalize_lang_code(source_lang)
            target = self._normalize_lang_code(target_lang)
            
            dict_key = f"{source}->{target}"
            if dict_key not in SIMPLE_DICTIONARY:
                logger.warning("Built-in dictionary does not support %s -> %s", source, target)
                return None
            
            dictionary = SIMPLE_DICTIONARY[dict_key]
            
            import re
            words = re.findall(r'[\w\u4e00-\u9fff]+|[^\w\s]', text.lower())
            
            translated_words = []
            translated_count = 0
            
            for word in words:
                if word in dictionary:
                    translated_words.append(dictionary[word])
                    translated_count += 1
                elif word in '.,!?;:\'"()-':
                    translated_words.append(word)
                else:
                    translated_words.append(word)
            
            if translated_count > 0:
                result = ' '.join(translated_words)
                logger.info("Built-in translated %d/%d words from %s to %s", translated_count, len(words), source, target)
                return result
            
            logger.debug("No words found in dictionary for: %s", text)
            return None
            
        except Exception as e:
            logger.error("Built-in translation failed: %s", e)
            return None
    
    def _translate_translatepy(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Translate using translatepy."""
        try:
            from translatepy import Translator as TranslatepyTranslator
            translator = TranslatepyTranslator()
            
            source = self._normalize_lang_code(source_lang)
            target = self._normalize_lang_code(target_lang)
            
            result = translator.translate(text, source_language=source, target_language=target)
            
            if result and result.result:
                logger.info("translatepy translated %d chars from %s to %s", len(text), source, target)
                return result.result
            
            logger.error("translatepy returned no result")
            return None
            
        except Exception as e:
            logger.error("translatepy translation failed: %s", e)
            return None
    
    def _translate_argos(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Translate using argostranslate."""
        try:
            source = self._normalize_lang_code(source_lang)
            target = self._normalize_lang_code(target_lang)
            
            cache_key = f"{source}->{target}:{text}"
            if cache_key in self._translation_cache:
                return self._translation_cache[cache_key]
            
            if not self._ensure_language_pair(source, target):
                logger.error("Could not install language pair %s -> %s", source, target)
                return None
            
            if self._installed_languages is None:
                self._installed_languages = argostranslate.translate.get_installed_languages()
            
            from_language = None
            to_language = None
            
            for lang in self._installed_languages:
                if lang.code == source:
                    from_language = lang
                if lang.code == target:
                    to_language = lang
            
            if from_language is None or to_language is None:
                logger.error("Languages not available after installation: %s, %s", source, target)
                return None
            
            translation = from_language.get_translation(to_language)
            if translation is None:
                logger.error("No translation found for %s -> %s", source, target)
                return None
            
            result = translation.translate(text)
            
            if len(self._translation_cache) < 1000:
                self._translation_cache[cache_key] = result
            
            logger.info("Offline translated %d chars from %s to %s", len(text), source, target)
            return result
            
        except Exception as e:
            logger.error("Offline translation failed: %s", e)
            return None


class AITranslator:
    """AI-based translator supporting multiple providers."""
    
    TRANSLATION_PROMPT = """You are a professional translator. Translate the following text from {source_lang} to {target_lang}. 
Only provide the translation, no explanations or additional text.
IMPORTANT: Preserve the original formatting - keep all line breaks, indentation, and structure exactly as in the original text.

Text to translate:
{text}

Translation:"""
    
    LANGUAGE_NAMES = {
        "en": "English",
        "zh-CN": "Simplified Chinese",
        "zh-TW": "Traditional Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "ru": "Russian",
        "pt": "Portuguese",
        "it": "Italian",
        "ar": "Arabic",
        "hi": "Hindi",
        "th": "Thai",
        "vi": "Vietnamese"
    }
    
    def __init__(self, provider: AIProvider):
        self.provider = provider
        self._client = None
    
    def _get_client(self):
        """Get the appropriate client based on provider type."""
        if self._client is None:
            if self.provider.provider_type == "ollama":
                self._client = OllamaClient(self.provider.api_url or OLLAMA_DEFAULT_URL)
            else:
                self._client = OpenAIClient(
                    self.provider.api_url or OPENAI_DEFAULT_URL,
                    self.provider.api_key
                )
        return self._client
    
    def _get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name."""
        return self.LANGUAGE_NAMES.get(lang_code, lang_code)
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Translate text using the AI provider."""
        client = self._get_client()
        
        source_name = self._get_language_name(source_lang)
        target_name = self._get_language_name(target_lang)
        
        prompt = self.TRANSLATION_PROMPT.format(
            source_lang=source_name,
            target_lang=target_name,
            text=text
        )
        
        messages = [{"role": "user", "content": prompt}]
        
        if self.provider.provider_type == "ollama":
            result = client.chat(self.provider.model, messages)
        else:
            result = client.chat(self.provider.model, messages)
        
        if result:
            import re
            result = result.strip()
            logger.debug("AI raw response: %s", result[:200])
            while '<think' in result.lower():
                start = result.lower().find('<think')
                end_tag = result.lower().find('</think', start)
                if end_tag != -1:
                    end = result.find('\n', end_tag)
                    if end == -1:
                        end = len(result)
                    result = result[:start] + result[end:]
                else:
                    break
            while '<thinking' in result.lower():
                start = result.lower().find('<thinking')
                end_tag = result.lower().find('</thinking', start)
                if end_tag != -1:
                    end = result.find('\n', end_tag)
                    if end == -1:
                        end = len(result)
                    result = result[:start] + result[end:]
                else:
                    break
            result = re.sub(r'\n{3,}', '\n\n', result)
            if target_lang.lower().startswith('zh') or target_lang.lower().startswith('ja'):
                lines = result.split('\n')
                processed_lines = []
                for line in lines:
                    processed_line = re.sub(r'[ \t]+', '', line)
                    processed_lines.append(processed_line)
                result = '\n'.join(processed_lines)
            result = re.sub(r'^["\'「」『』]|["\'「」『』]$', '', result)
        
        return result
    
    def test_connection(self) -> tuple:
        """Test the connection to the AI provider."""
        client = self._get_client()
        
        if self.provider.provider_type == "ollama":
            if client.is_running():
                models = client.list_models()
                if any(m["name"] == self.provider.model or m["name"].startswith(self.provider.model + ":") for m in models):
                    return True, f"Connected to Ollama. Model '{self.provider.model}' available."
                else:
                    return False, f"Ollama running but model '{self.provider.model}' not found."
            else:
                return False, "Cannot connect to Ollama. Make sure it's running."
        else:
            result = client.chat(self.provider.model, [{"role": "user", "content": "Hi"}])
            if result:
                return True, f"Successfully connected to {self.provider.name}."
            else:
                return False, f"Failed to connect to {self.provider.name}. Check API key and URL."


def get_ollama_models(base_url: str = OLLAMA_DEFAULT_URL) -> List[Dict[str, Any]]:
    """Get list of available Ollama models."""
    client = OllamaClient(base_url)
    return client.list_models()


def is_ollama_running(base_url: str = OLLAMA_DEFAULT_URL) -> bool:
    """Check if Ollama is running."""
    client = OllamaClient(base_url)
    return client.is_running()


def get_default_providers() -> List[Dict[str, Any]]:
    """Get list of default/predefined AI providers."""
    return [
        {
            "name": "DeepSeek Chat",
            "provider_type": "openai_compatible",
            "api_url": "https://api.deepseek.com/v1",
            "api_key": "",
            "model": "deepseek-chat",
            "model_type": "chat"
        },
        {
            "name": "DeepSeek Reasoner",
            "provider_type": "openai_compatible",
            "api_url": "https://api.deepseek.com/v1",
            "api_key": "",
            "model": "deepseek-reasoner",
            "model_type": "chat"
        },
        {
            "name": "Moonshot AI (Kimi)",
            "provider_type": "openai_compatible",
            "api_url": "https://api.moonshot.cn/v1",
            "api_key": "",
            "model": "moonshot-v1-8k",
            "model_type": "chat"
        },
        {
            "name": "Zhipu AI (GLM)",
            "provider_type": "openai_compatible",
            "api_url": "https://open.bigmodel.cn/api/paas/v4",
            "api_key": "",
            "model": "glm-4",
            "model_type": "chat"
        },
        {
            "name": "Alibaba Qwen",
            "provider_type": "openai_compatible",
            "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": "",
            "model": "qwen-turbo",
            "model_type": "chat"
        },
        {
            "name": "Baidu ERNIE",
            "provider_type": "openai_compatible",
            "api_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat",
            "api_key": "",
            "model": "ernie-4.0-8k",
            "model_type": "chat"
        },
        {
            "name": "Tencent Hunyuan",
            "provider_type": "openai_compatible",
            "api_url": "https://api.hunyuan.cloud.tencent.com/v1",
            "api_key": "",
            "model": "hunyuan-lite",
            "model_type": "chat"
        },
        {
            "name": "ByteDance Doubao",
            "provider_type": "openai_compatible",
            "api_url": "https://ark.cn-beijing.volces.com/api/v3",
            "api_key": "",
            "model": "doubao-pro-4k",
            "model_type": "chat"
        },
        {
            "name": "Minimax",
            "provider_type": "openai_compatible",
            "api_url": "https://api.minimax.chat/v1",
            "api_key": "",
            "model": "abab5.5-chat",
            "model_type": "chat"
        },
        {
            "name": "SiliconFlow",
            "provider_type": "openai_compatible",
            "api_url": "https://api.siliconflow.cn/v1",
            "api_key": "",
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "model_type": "chat"
        },
        {
            "name": "OpenAI GPT-4",
            "provider_type": "openai",
            "api_url": OPENAI_DEFAULT_URL,
            "api_key": "",
            "model": "gpt-4",
            "model_type": "chat"
        },
        {
            "name": "OpenAI GPT-3.5 Turbo",
            "provider_type": "openai",
            "api_url": OPENAI_DEFAULT_URL,
            "api_key": "",
            "model": "gpt-3.5-turbo",
            "model_type": "chat"
        },
        {
            "name": "Anthropic Claude",
            "provider_type": "openai_compatible",
            "api_url": "https://api.anthropic.com/v1",
            "api_key": "",
            "model": "claude-3-opus-20240229",
            "model_type": "chat"
        },
        {
            "name": "Groq",
            "provider_type": "openai_compatible",
            "api_url": "https://api.groq.com/openai/v1",
            "api_key": "",
            "model": "llama3-8b-8192",
            "model_type": "chat"
        },
        {
            "name": "Together AI",
            "provider_type": "openai_compatible",
            "api_url": "https://api.together.xyz/v1",
            "api_key": "",
            "model": "meta-llama/Llama-3-8b-chat-hf",
            "model_type": "chat"
        },
        {
            "name": "OpenRouter",
            "provider_type": "openai_compatible",
            "api_url": "https://openrouter.ai/api/v1",
            "api_key": "",
            "model": "openai/gpt-3.5-turbo",
            "model_type": "chat"
        },
    ]


_offline_translator_instance = None

def get_offline_translator() -> OfflineTranslator:
    """Get or create the global offline translator instance."""
    global _offline_translator_instance
    if _offline_translator_instance is None:
        _offline_translator_instance = OfflineTranslator()
    return _offline_translator_instance


def is_offline_available() -> bool:
    """Check if offline translation is available."""
    return OFFLINE_TRANSLATOR_AVAILABLE


def get_offline_languages() -> List[Dict[str, Any]]:
    """Get list of installed offline translation language pairs."""
    translator = get_offline_translator()
    return translator.get_installed_languages()


def get_offline_available_packages() -> List[Dict[str, Any]]:
    """Get list of available offline translation packages."""
    translator = get_offline_translator()
    return translator.get_available_packages()


def install_offline_language(from_code: str, to_code: str) -> bool:
    """Install an offline translation language pair."""
    translator = get_offline_translator()
    return translator.install_language_pair(from_code, to_code)
