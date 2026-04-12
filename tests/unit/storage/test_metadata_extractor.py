# -*- coding: utf-8 -*-
"""
测试 Phase 3: 元数据抽取器 - MetadataExtractor
"""
import pytest
from copaw.storage import MetadataExtractor


class TestMetadataExtractor:
    """测试元数据抽取器"""

    def test_extract_agent_config(self):
        """测试Agent配置抽取"""
        data = {
            "id": "agent-001",
            "name": "Test Agent",
            "description": "A test agent",
            "model_provider": "openai",
            "model_name": "gpt-4",
            "model_base_url": "https://api.openai.com",
            "temperature": 0.7,
            "max_tokens": 2000,
            "memory_backend": "postgres",
            "memory_max_messages": 50,
            "skills": ["web_search", "code_runner"],
        }

        extracted = MetadataExtractor.extract_agent_config(data)

        assert extracted["agent_id"] == "agent-001"
        assert extracted["name"] == "Test Agent"
        assert extracted["model_provider"] == "openai"
        assert extracted["model_name"] == "gpt-4"
        assert extracted["temperature"] == 0.7
        assert extracted["max_tokens"] == 2000
        assert extracted["skills"] == ["web_search", "code_runner"]

    def test_extract_conversations(self):
        """测试对话抽取"""
        data = {
            "chat-001": {
                "title": "Test Chat",
                "started_at": "2024-01-01T10:00:00Z",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello",
                        "timestamp": "2024-01-01T10:00:00Z",
                    },
                    {
                        "role": "assistant",
                        "content": "Hi there!",
                        "timestamp": "2024-01-01T10:00:01Z",
                        "token_count": 10,
                    },
                ],
            },
        }

        extracted = MetadataExtractor.extract_conversations(data)

        assert len(extracted) == 1
        conv = extracted[0]
        assert conv["chat_id"] == "chat-001"
        assert conv["title"] == "Test Chat"
        assert conv["message_count"] == 2

    def test_extract_skill_config(self):
        """测试Skill配置抽取"""
        data = {
            "name": "web_search",
            "display_name": "Web Search",
            "description": "Search the web",
            "version": "1.0.0",
            "author": "copaw",
        }

        extracted = MetadataExtractor.extract_skill_config(data)

        assert extracted["skill_name"] == "web_search"
        assert extracted["display_name"] == "Web Search"
        assert extracted["version"] == "1.0.0"

    def test_extract_memory_document(self):
        """测试记忆文档抽取"""
        content = """# MEMORY - January 2024

## Key Points
- Point 1
- Point 2

## Tags
#important #review
"""
        extracted = MetadataExtractor.extract_memory_document(content)

        assert extracted["title"] == "MEMORY - January 2024"
        assert "Key Points" in extracted["headings"]
        assert "Tags" in extracted["headings"]

    def test_extract_token_usage(self):
        """测试Token使用统计抽取"""
        data = {
            "2024-01-01": {
                "prompt_tokens": 1000,
                "completion_tokens": 500,
                "total_tokens": 1500,
                "request_count": 10,
                "cost_usd": 0.05,
            },
        }

        extracted = MetadataExtractor.extract_token_usage(data)

        assert len(extracted) == 1
        stat = extracted[0]
        assert stat["stat_date"] == "2024-01-01"
        assert stat["prompt_tokens"] == 1000
        assert stat["completion_tokens"] == 500
        assert stat["total_tokens"] == 1500

    def test_categorize_file(self):
        """测试文件分类"""
        assert MetadataExtractor.categorize_file("agent.json") == "workspace"
        assert MetadataExtractor.categorize_file("skill.json") == "skill"
        assert MetadataExtractor.categorize_file("MEMORY.md") == "memory"
        assert MetadataExtractor.categorize_file("chats.json") == "workspace"
        assert MetadataExtractor.categorize_file("token_usage.json") == "analytics"

    def test_compute_content_hash(self):
        """测试内容哈希计算"""
        content = b"Hello, World!"
        hash1 = MetadataExtractor.compute_content_hash(content)
        hash2 = MetadataExtractor.compute_content_hash(content)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256

    def test_extract_from_json_file(self):
        """测试从JSON文件抽取"""
        import json
        import tempfile
        from pathlib import Path

        data = {"name": "Test", "version": "1.0"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            extracted, content_hash = MetadataExtractor.extract_from_file(Path(temp_path), "workspace")
            assert extracted is not None
            assert content_hash is not None
        finally:
            Path(temp_path).unlink()
