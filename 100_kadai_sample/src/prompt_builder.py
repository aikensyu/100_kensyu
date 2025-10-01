"""
処理概要:
    - スプレッドシートから取得したテンプレート文字列と自社情報を組み合わせて、企業調査および営業文作成用のプロンプトを生成します。
    - `{{company_name}}`, `{{company_url}}`, `{{num_employees}}`, `{{company_description}}`, `{{registered_company_name}}`,
      `{{registered_company_name_encoded}}`, `{{company_name_encoded}}`, `{{self_info}}` などのプレースホルダを辞書から置換するだけのシンプルな仕組みです。
使用方法:
    - `PromptBuilder` に検索用テンプレート、営業文テンプレート、自社紹介文（単一セル）を渡します。
    - `render_search_prompt` / `render_message_prompt` に企業情報の辞書を渡すと、Claude/OpenAIへ送る文字列を取得できます。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping

PLACEHOLDER_PREFIX = "{{"
PLACEHOLDER_SUFFIX = "}}"


@dataclass
class PromptBuilder:
    """Render prompts for company research and outreach message."""

    search_template: str
    message_template: str
    self_info: str

    def render_search_prompt(self, company: Mapping[str, str]) -> str:
        """Return search prompt text; fallback to company URL or name when template is empty."""
        replacements = self._base_replacements(company)
        prompt = self._substitute(self.search_template, replacements)
        fallback = company.get("company_url") or company.get("company_name", "")
        return prompt.strip() or fallback

    def render_message_prompt(self, company: Mapping[str, str], company_description: str) -> str:
        """Return outreach prompt filled with company description and self info."""
        replacements = self._base_replacements(company)
        replacements["company_description"] = company_description
        return self._substitute(self.message_template, replacements)

    def _substitute(self, template: str, replacements: Dict[str, str]) -> str:
        """Naive placeholder substitution using {{key}} markers."""
        result = template
        for key, value in replacements.items():
            placeholder = f"{PLACEHOLDER_PREFIX}{key}{PLACEHOLDER_SUFFIX}"
            result = result.replace(placeholder, value)
        return result

    def _base_replacements(self, company: Mapping[str, str]) -> Dict[str, str]:
        """Return common replacements shared across prompts."""
        return {
            "company_name": company.get("company_name", ""),
            "company_name_encoded": company.get("company_name_encoded", ""),
            "company_url": company.get("company_url", ""),
            "num_employees": company.get("num_employees", ""),
            "contact_form_url": company.get("contact_form_url", ""),
            "address": company.get("address", ""),
            "prefecture_id": company.get("prefecture_id", ""),
            "registered_company_name": company.get("registered_company_name", ""),
            "registered_company_name_encoded": company.get("registered_company_name_encoded", ""),
            "self_info": self.self_info,
        }
