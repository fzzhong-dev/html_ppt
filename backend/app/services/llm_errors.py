"""User-facing messages for common LLM HTTP/SDK failures."""

from __future__ import annotations


def format_llm_error(exc: BaseException) -> str:
    raw = str(exc).strip()
    low = raw.lower()

    try:
        from openai import APIConnectionError, APITimeoutError

        if isinstance(exc, (APIConnectionError, APITimeoutError)):
            return (
                "无法连接到模型服务（超时或网络中断）。"
                "请检查能否访问对应 API 域名、防火墙与公司代理；"
                "若在终端设置了 HTTPS_PROXY 且代理不稳定，可在 backend/.env 设置 LLM_TRUST_ENV_PROXY=false 尝试直连。"
                "也可增大 LLM_CONNECT_TIMEOUT_SECONDS / LLM_HTTP_TIMEOUT_SECONDS。"
            )
    except ImportError:
        pass

    if "connection error" in low or "connecttimeout" in low.replace(" ", "") or "timed out" in low:
        return (
            "无法连接到模型服务（网络超时或连接被拒绝）。"
            "请检查网络与代理，或在 .env 中设置 LLM_TRUST_ENV_PROXY=false、调整超时变量。"
        )

    if "余额不足" in raw or "无可用资源包" in raw or "1113" in raw:
        return (
            "智谱接口返回：账号余额不足或无可用资源包（错误码 1113）。"
            "请到 open.bigmodel.cn 充值或领取资源包，或在 .env 中切换 DEFAULT_PROVIDER。"
        )

    if "429" in raw and ("rate" in low or "limit" in low):
        return "请求过于频繁或被限流（429），请稍后再试或更换模型。"

    if "401" in raw or "403" in raw or "invalid" in low and "key" in low:
        return "API Key 无效或无权访问，请检查 .env 中的密钥与权限。"

    if len(raw) > 600:
        return raw[:600] + "…"
    return raw or "模型调用失败，请稍后重试。"
