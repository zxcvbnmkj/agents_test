"""可选的 Phoenix tracing 初始化。

Pydantic AI 和 LangChain/LangGraph 共用一个 OTel provider；缺少 Phoenix
或 instrumentation 依赖时不影响正常评测。
"""

from __future__ import annotations

import logging
import socket
from urllib.parse import urlparse

import config

logger = logging.getLogger(__name__)
_provider = None


def _provider_for_phoenix():
    global _provider
    if _provider is not None:
        return _provider
    url = getattr(config, 'PHOENIX_ENDPOINT', None)
    if not url or not _listening(url):
        return None
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning('Phoenix 已配置但 OTel 依赖未安装，跳过 tracing')
        return None
    _provider = TracerProvider()
    _provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f'{url}/v1/traces')))
    return _provider


def setup_pydantic() -> None:
    provider = _provider_for_phoenix()
    if provider is None:
        return
    try:
        from openinference.instrumentation.pydantic_ai import OpenInferenceSpanProcessor
        from pydantic_ai import Agent, InstrumentationSettings
        provider.add_span_processor(OpenInferenceSpanProcessor())
        Agent.instrument_all(InstrumentationSettings(tracer_provider=provider))
        logger.info('Pydantic AI tracing 已接入 Phoenix: %s', config.PHOENIX_ENDPOINT)
    except ImportError:
        logger.warning('缺少 Pydantic AI Phoenix instrumentation，跳过 tracing')


def setup_langchain() -> None:
    provider = _provider_for_phoenix()
    if provider is None:
        return
    try:
        from openinference.instrumentation.langchain import LangChainInstrumentor
        LangChainInstrumentor().instrument(tracer_provider=provider)
        logger.info('LangGraph/LangChain tracing 已接入 Phoenix: %s', config.PHOENIX_ENDPOINT)
    except ImportError:
        logger.warning('缺少 LangChain Phoenix instrumentation，跳过 tracing')


def _listening(url: str) -> bool:
    parsed = urlparse(url)
    try:
        with socket.create_connection((parsed.hostname, parsed.port), timeout=0.2):
            return True
    except OSError:
        return False
