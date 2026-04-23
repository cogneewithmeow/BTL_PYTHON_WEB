import json
import os
import urllib.request
import urllib.error
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional


ChatMessage = Dict[str, str]  # {"role": "user"|"assistant", "content": "..."}


@dataclass
class ChatReply:
    reply: str
    provider: str


class ChatProviderError(Exception):
    pass


class ChatProvider:
    provider_name: str = "base"

    def chat(self, *, message: str, history: List[ChatMessage], user_label: Optional[str] = None) -> ChatReply:
        raise NotImplementedError


logger = logging.getLogger(__name__)


class OpenRouterChatProvider(ChatProvider):
    provider_name = "openrouter"

    def __init__(self) -> None:
        # Yêu cầu: đọc từ env, không hardcode key trong source.
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.model = os.environ.get("OPENAI_MODEL", "openai/gpt-4o-mini")
        # Yêu cầu: base_url cố định theo OpenRouter
        self.base_url = "https://openrouter.ai/api/v1"

    def _build_messages(self, *, message: str, history: List[ChatMessage], user_label: Optional[str]) -> List[dict]:
        system = (
            "Bạn là trợ lý AI cho website bán hàng đồ ăn 'Ăn là Ghiền'. "
            "Hãy trả lời ngắn gọn, thân thiện, dễ hiểu bằng tiếng Việt. "
            "Nếu thiếu dữ liệu cụ thể (giá, tồn kho, đơn hàng), hãy hỏi lại hoặc hướng dẫn người dùng kiểm tra trong website. "
            "Không bịa đặt thông tin. "
            "Ưu tiên gợi ý thao tác (ví dụ: vào Giỏ hàng, Checkout, Trang cá nhân)."
        )
        if user_label:
            system += f" Người dùng hiện tại: {user_label}."

        msgs: List[dict] = [{"role": "system", "content": system}]

        for m in history[-20:]:
            role = m.get("role")
            content = m.get("content")
            if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
                msgs.append({"role": role, "content": content.strip()})

        msgs.append({"role": "user", "content": message})
        return msgs

    def _parse_provider_error_detail(self, raw: str) -> str:
        """
        OpenRouter thường trả JSON dạng:
        {"error":{"message":"...", "type":"...", "code":"..."}}
        """
        if not raw:
            return ""
        try:
            obj = json.loads(raw)
        except Exception:
            return raw[:500]

        err = obj.get("error") if isinstance(obj, dict) else None
        if isinstance(err, dict):
            msg = err.get("message") or ""
            code = err.get("code") or ""
            typ = err.get("type") or ""
            parts = [p for p in [str(code).strip(), str(typ).strip(), str(msg).strip()] if p]
            return " | ".join(parts)[:800]
        return raw[:500]

    def _raise_http_error(self, *, status: int, detail: str) -> None:
        model = (self.model or "").strip()
        base = self.base_url

        if status in (401, 403):
            raise ChatProviderError(f"OpenRouter auth failed ({status}). Check OPENAI_API_KEY. Detail: {detail}".strip())
        if status == 402:
            raise ChatProviderError(f"OpenRouter 402 Payment Required (insufficient credits). Detail: {detail}".strip())
        if status == 404:
            # OpenRouter có thể trả 404 cho model/route
            raise ChatProviderError(f"OpenRouter 404 Not Found. Model may not exist: {model}. Detail: {detail}".strip())
        if status == 429:
            raise ChatProviderError(f"OpenRouter rate limit/quota exceeded (429). Detail: {detail}".strip())
        if status >= 500:
            raise ChatProviderError(f"OpenRouter server error ({status}). Detail: {detail}".strip())

        raise ChatProviderError(f"OpenRouter HTTPError {status}. Detail: {detail}".strip())

    def chat(self, *, message: str, history: List[ChatMessage], user_label: Optional[str] = None) -> ChatReply:
        api_key = (self.api_key or "").strip()
        if not api_key:
            # Yêu cầu: báo lỗi rõ ràng ở server log
            logger.error("Missing OPENAI_API_KEY. Set environment variable OPENAI_API_KEY to your OpenRouter key.")
            raise ChatProviderError("Missing OPENAI_API_KEY")

        model = (self.model or "").strip()
        if not model:
            logger.error("Missing OPENAI_MODEL. Set environment variable OPENAI_MODEL (e.g. openai/gpt-4o-mini).")
            raise ChatProviderError("Missing OPENAI_MODEL")

        url = f"{self.base_url}/chat/completions"
        body = {
            "model": model,
            "messages": self._build_messages(message=message, history=history, user_label=user_label),
            "temperature": 0.3,
        }
        data = json.dumps(body).encode("utf-8")

        # Log ngữ cảnh quan trọng cho debug (không log api_key)
        logger.info("OpenRouter request: base_url=%s model=%s message_len=%s history_len=%s", self.base_url, model, len(message), len(history))

        req = urllib.request.Request(
            url=url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                # Optional nhưng hữu ích (không bắt buộc): OpenRouter recommend headers
                "X-Title": "AnLaGhien Django Chatbot",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode("utf-8")
            except Exception:
                detail = ""
            parsed_detail = self._parse_provider_error_detail(detail) or str(e)
            logger.warning(
                "OpenRouter HTTPError: status=%s base_url=%s model=%s detail=%s",
                getattr(e, "code", "?"),
                self.base_url,
                model,
                parsed_detail,
                exc_info=True,
            )
            self._raise_http_error(status=int(getattr(e, "code", 0) or 0), detail=parsed_detail)
        except urllib.error.URLError as e:
            logger.warning("OpenRouter connection error: base_url=%s model=%s err=%s", self.base_url, model, str(e), exc_info=True)
            raise ChatProviderError(f"OpenRouter request failed (network): {str(e)}") from e

        parsed = json.loads(raw)
        try:
            reply = parsed["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(
                "OpenRouter invalid response: base_url=%s model=%s raw=%s",
                self.base_url,
                model,
                (raw or "")[:800],
                exc_info=True,
            )
            raise ChatProviderError("Không đọc được phản hồi từ AI provider.") from e

        reply_text = (reply or "").strip()
        if not reply_text:
            logger.warning("OpenRouter returned empty reply: base_url=%s model=%s raw=%s", self.base_url, model, (raw or "")[:800])
            raise ChatProviderError("AI provider trả về nội dung rỗng.")

        return ChatReply(reply=reply_text, provider=self.provider_name)


def get_chat_provider() -> ChatProvider:
    # Hiện tại mặc định dùng OpenRouter theo yêu cầu dự án.
    return OpenRouterChatProvider()


def chat_reply(*, message: str, history: List[ChatMessage], user_label: Optional[str] = None) -> ChatReply:
    provider = get_chat_provider()
    return provider.chat(message=message, history=history, user_label=user_label)

