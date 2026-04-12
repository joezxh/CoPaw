# -*- coding: utf-8 -*-
"""
Metadata Extractor — 元数据抽取器

双轨存储核心组件，负责：
1. 通用文件索引: 所有文件 → storage_objects
2. 业务结构化抽取: 特定文件 → 专用元数据表
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import PurePosixPath
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """元数据抽取器 — 双轨存储核心组件"""

    # 按文件扩展名和路径模式的分类规则
    CATEGORY_RULES = {
        # Agent 配置
        "agent.json": "workspace",
        "chats.json": "workspace",
        "jobs.json": "workspace",
        "token_usage.json": "workspace",
        "skill.json": "workspace",
        # 人格文件
        "MEMORY.md": "memory",
        "AGENTS.md": "workspace",
        "SOUL.md": "workspace",
        "PROFILE.md": "workspace",
        "HEARTBEAT.md": "workspace",
        "BOOTSTRAP.md": "workspace",
        # 技能文件
        "SKILL.md": "skill",
        # 媒体文件
        ".png": "media",
        ".jpg": "media",
        ".jpeg": "media",
        ".gif": "media",
        ".mp4": "media",
        ".mp3": "media",
        ".wav": "media",
        # 模型文件
        ".gguf": "model",
        ".bin": "model",
        # 配置文件
        "config.json": "config",
    }

    @classmethod
    def extract_category(cls, key: str) -> str:
        """从对象键推断文件类别"""
        path = PurePosixPath(key)
        name = path.name
        suffix = path.suffix.lower()

        # 精确匹配文件名
        if name in cls.CATEGORY_RULES:
            return cls.CATEGORY_RULES[name]

        # 匹配扩展名
        if suffix in cls.CATEGORY_RULES:
            return cls.CATEGORY_RULES[suffix]

        # 路径模式匹配
        parts = path.parts
        if "skills" in parts:
            return "skill"
        if "memory" in parts:
            return "memory"
        if "media" in parts:
            return "media"
        if "models" in parts or "model" in parts:
            return "model"
        if "workspaces" in parts:
            return "workspace"

        return "other"

    @classmethod
    def extract_search_text(cls, key: str, content: bytes) -> str:
        """从文件内容中提取可搜索的文本"""
        path = PurePosixPath(key)
        suffix = path.suffix.lower()

        if suffix == ".json":
            try:
                data = json.loads(content)
                return cls._flatten_json_values(data)
            except Exception as e:
                logger.warning("Failed to parse JSON for search text: %s", e)
                return ""
        elif suffix in (".md", ".txt", ".csv"):
            try:
                return content.decode("utf-8")[:10000]  # 截断
            except Exception:
                return ""
        else:
            return path.stem  # 二进制文件仅索引文件名

    @classmethod
    def extract_agent_config(cls, data: dict) -> dict:
        """从 agent.json 抽取结构化字段"""
        try:
            model_cfg = data.get("model", {})
            channels = data.get("channels", {})
            enabled_channels = [
                ch for ch, cfg in channels.items()
                if isinstance(cfg, dict) and cfg.get("enabled", False)
            ]
            skills = data.get("skills", [])
            if isinstance(skills, list):
                skill_names = [s.get("name", s) if isinstance(s, dict) else s for s in skills]
            else:
                skill_names = []

            return {
                "name": data.get("name", "Unknown"),
                "description": data.get("description"),
                "model_provider": model_cfg.get("provider") if isinstance(model_cfg, dict) else None,
                "model_name": model_cfg.get("model") if isinstance(model_cfg, dict) else None,
                "model_base_url": model_cfg.get("base_url") if isinstance(model_cfg, dict) else None,
                "temperature": model_cfg.get("temperature") if isinstance(model_cfg, dict) else None,
                "max_tokens": model_cfg.get("max_tokens") if isinstance(model_cfg, dict) else None,
                "enabled_channels": enabled_channels,
                "memory_backend": data.get("memory", {}).get("backend") if isinstance(data.get("memory"), dict) else None,
                "memory_max_messages": data.get("memory", {}).get("max_messages") if isinstance(data.get("memory"), dict) else None,
                "skills": skill_names,
                "heartbeat_enabled": data.get("heartbeat", {}).get("enabled") if isinstance(data.get("heartbeat"), dict) else None,
                "heartbeat_every": data.get("heartbeat", {}).get("every") if isinstance(data.get("heartbeat"), dict) else None,
            }
        except Exception as e:
            logger.warning("Failed to extract agent config: %s", e)
            return {"name": data.get("name", "Unknown")}

    @classmethod
    def extract_skill_config(cls, data: dict) -> dict:
        """从 skill.json 抽取结构化字段"""
        try:
            return {
                "skill_name": data.get("name", "Unknown"),
                "display_name": data.get("display_name"),
                "description": data.get("description"),
                "version": data.get("version", "1.0.0"),
                "source": data.get("source", "user"),
                "category": data.get("category"),
                "enabled": data.get("enabled", True),
                "channels": data.get("channels", []),
            }
        except Exception as e:
            logger.warning("Failed to extract skill config: %s", e)
            return {"skill_name": data.get("name", "Unknown"), "version": "1.0.0"}

    @classmethod
    def extract_conversations(cls, data: dict) -> list[dict]:
        """从 chats.json 抽取对话和消息"""
        results = []
        try:
            chats = data.get("chats", [])
            if not isinstance(chats, list):
                return results

            for chat in chats:
                if not isinstance(chat, dict):
                    continue
                messages = chat.get("messages", [])
                conv_data = {
                    "chat_id": chat.get("id", chat.get("chat_id", "")),
                    "title": chat.get("title"),
                    "message_count": len(messages) if isinstance(messages, list) else 0,
                    "messages": [],
                }

                if isinstance(messages, list):
                    for msg in messages:
                        if not isinstance(msg, dict):
                            continue
                        conv_data["messages"].append({
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", ""),
                            "timestamp": msg.get("timestamp") or msg.get("created_at"),
                            "tool_calls": msg.get("tool_calls"),
                            "tool_call_id": msg.get("tool_call_id"),
                            "token_count": msg.get("token_count"),
                            "metadata": msg.get("metadata", {}),
                        })

                results.append(conv_data)
        except Exception as e:
            logger.warning("Failed to extract conversations: %s", e)
        return results

    @classmethod
    def extract_token_usage(cls, data: dict) -> list[dict]:
        """从 token_usage.json 按日分桶抽取"""
        results = []
        try:
            usage_records = data.get("usage", [])
            if not isinstance(usage_records, list):
                return results

            daily_stats: dict[str, dict] = {}
            for record in usage_records:
                if not isinstance(record, dict):
                    continue
                date_str = record.get("date", record.get("timestamp", ""))[:10]
                if not date_str:
                    continue

                if date_str not in daily_stats:
                    daily_stats[date_str] = {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "request_count": 0,
                        "cost_usd": 0.0,
                        "model_provider": record.get("provider") or record.get("model_provider"),
                        "model_name": record.get("model") or record.get("model_name"),
                    }

                stats = daily_stats[date_str]
                stats["prompt_tokens"] += record.get("prompt_tokens", 0)
                stats["completion_tokens"] += record.get("completion_tokens", 0)
                stats["total_tokens"] += record.get("total_tokens", 0)
                stats["request_count"] += 1
                stats["cost_usd"] += record.get("cost", 0.0)

            results = [{"stat_date": k, **v} for k, v in daily_stats.items()]
        except Exception as e:
            logger.warning("Failed to extract token usage: %s", e)
        return results

    @classmethod
    def extract_memory_document(cls, content: str, doc_type: str) -> dict:
        """从 Markdown 抽取标题/标签/摘要"""
        try:
            headings = cls._parse_markdown_headings(content)
            tags = cls._extract_markdown_tags(content)
            summary = content[:500].strip()

            # 尝试提取日期 (针对 memory_daily 类型)
            doc_date = None
            if doc_type == "memory_daily":
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', content[:200])
                if date_match:
                    doc_date = date_match.group(1)

            return {
                "doc_type": doc_type,
                "doc_date": doc_date,
                "title": headings[0] if headings else None,
                "summary": summary,
                "headings": headings,
                "tags": tags,
            }
        except Exception as e:
            logger.warning("Failed to extract memory document: %s", e)
            return {"doc_type": doc_type, "summary": content[:500] if content else ""}

    @staticmethod
    def _flatten_json_values(data: Any, depth: int = 0, max_depth: int = 3) -> str:
        """递归提取 JSON 中所有字符串值"""
        if depth > max_depth:
            return ""
        parts = []
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str) and len(v) < 500:
                    parts.append(v)
                elif isinstance(v, (dict, list)):
                    parts.append(MetadataExtractor._flatten_json_values(v, depth + 1))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str) and len(item) < 500:
                    parts.append(item)
                elif isinstance(item, (dict, list)):
                    parts.append(MetadataExtractor._flatten_json_values(item, depth + 1))
        return " ".join(parts)

    @staticmethod
    def _parse_markdown_headings(content: str) -> list[str]:
        """提取 Markdown 标题"""
        headings = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                heading = line.lstrip("#").strip()
                if heading:
                    headings.append(heading)
        return headings

    @staticmethod
    def _extract_markdown_tags(content: str) -> list[str]:
        """从 Markdown 中提取标签 (tags: tag1, tag2)"""
        tags = []
        for line in content.split("\n")[:20]:  # 仅检查前20行
            if line.lower().startswith("tags:"):
                tag_str = line[5:].strip()
                tags = [t.strip() for t in tag_str.split(",") if t.strip()]
                break
        return tags

    @staticmethod
    def compute_content_hash(data: bytes) -> str:
        """计算 SHA-256 内容哈希"""
        return hashlib.sha256(data).hexdigest()
