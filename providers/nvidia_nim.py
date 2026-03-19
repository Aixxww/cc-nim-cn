"""NVIDIA NIM provider - optimized for streaming and memory safety."""

import logging
import os
import json
import uuid
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from .base import BaseProvider, ProviderConfig
from .utils import (
    SSEBuilder,
    map_stop_reason,
    ThinkTagParser,
    HeuristicToolParser,
    ContentType,
)
from .exceptions import APIError
from .nvidia_mixins import (
    RequestBuilderMixin,
    ErrorMapperMixin,
    ResponseConverterMixin,
)
from .rate_limit import GlobalRateLimiter

logger = logging.getLogger(__name__)


class NvidiaNimProvider(
    RequestBuilderMixin,
    ErrorMapperMixin,
    ResponseConverterMixin,
    BaseProvider,
):
    """NVIDIA NIM provider using official OpenAI client.

    Memory-safe implementation with proper resource cleanup.
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._api_key = config.api_key or os.getenv("NVIDIA_NIM_API_KEY", "")
        self._base_url = (
            config.base_url
            or os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
        ).rstrip("/")
        self._nim_params = self._load_nim_params()
        self._global_rate_limiter = GlobalRateLimiter.get_instance()

        # Create AsyncOpenAI client with connection limits
        # These settings help prevent memory buildup from accumulated connections
        self._client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            max_retries=2,
            timeout=300.0,
            # Connection pool limits to prevent unbounded connection growth
            http_client=None,  # Use default httpx client with built-in limits
        )

        logger.info(
            f"NvidiaNimProvider initialized: base_url={self._base_url}, "
            f"model_params={list(self._nim_params.keys())}"
        )

    async def stream_response(
        self, request: Any, input_tokens: int = 0
    ) -> AsyncIterator[str]:
        """Stream response in Anthropic SSE format.

        Memory-safe implementation with proper cleanup on client disconnect.
        """
        # Wait if globally rate limited
        waited_reactively = await self._global_rate_limiter.wait_if_blocked()

        message_id = f"msg_{uuid.uuid4().hex}"
        sse = SSEBuilder(message_id, request.model, input_tokens)

        if waited_reactively:
            error_msg = "⏱️ Rate limit active. Retrying..."
            logger.info(f"NIM_STREAM: {message_id} - reactive wait, notifying")
            yield sse.message_start()
            for event in sse.emit_error(error_msg):
                yield event
            # Early return - no need to continue after rate limit notification
            return

        body = self._build_request_body(request, stream=True)
        logger.info(
            f"NIM_STREAM: {message_id} - model={body.get('model')} "
            f"msgs={len(body.get('messages', []))} "
            f"tools={len(body.get('tools', []))}"
        )

        # Emit message_start
        yield sse.message_start()

        # Create parsers locally - they'll be garbage collected after function exit
        think_parser = ThinkTagParser()
        heuristic_parser = HeuristicToolParser()

        finish_reason = None
        usage_info = None
        error_occurred = False

        try:
            # Create stream with context manager for proper cleanup
            stream = await self._client.chat.completions.create(**body, stream=True)

            async for chunk in stream:
                if getattr(chunk, "usage", None):
                    usage_info = chunk.usage

                if not chunk.choices:
                    continue

                choice = chunk.choices[0]
                delta = choice.delta

                if choice.finish_reason:
                    finish_reason = choice.finish_reason
                    logger.debug(f"NIM finish_reason: {finish_reason}")

                # Handle reasoning content
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    for event in sse.ensure_thinking_block():
                        yield event
                    yield sse.emit_thinking_delta(reasoning)

                # Handle text content
                if delta.content:
                    for part in think_parser.feed(delta.content):
                        if part.type == ContentType.THINKING:
                            for event in sse.ensure_thinking_block():
                                yield event
                            yield sse.emit_thinking_delta(part.content)
                        else:
                            filtered_text, detected_tools = heuristic_parser.feed(part.content)

                            if filtered_text:
                                for event in sse.ensure_text_block():
                                    yield event
                                yield sse.emit_text_delta(filtered_text)

                            for tool_use in detected_tools:
                                for event in sse.close_content_blocks():
                                    yield event

                                block_idx = sse.blocks.allocate_index()
                                yield sse.content_block_start(
                                    block_idx,
                                    "tool_use",
                                    id=tool_use["id"],
                                    name=tool_use["name"],
                                )
                                yield sse.content_block_delta(
                                    block_idx,
                                    "input_json_delta",
                                    json.dumps(tool_use["input"]),
                                )
                                yield sse.content_block_stop(block_idx)

                # Handle native tool calls
                if delta.tool_calls:
                    for event in sse.close_content_blocks():
                        yield event
                    for tc in delta.tool_calls:
                        tc_info = {
                            "index": tc.index,
                            "id": tc.id,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for event in self._process_tool_call(tc_info, sse, message_id):
                            yield event

        except Exception as e:
            logger.error(f"NIM_ERROR: {message_id} - {type(e).__name__}: {e}")
            mapped_e = self._map_error(e)
            error_occurred = True

            # Ensure open blocks are closed before emitting error
            for event in sse.close_content_blocks():
                yield event

            # Extract error message from mapped exception
            error_message = str(getattr(mapped_e, "message", mapped_e))
            logger.info(f"NIM_STREAM: {message_id} - emitting error event")
            for event in sse.emit_error(error_message):
                yield event

        finally:
            # Flush remaining content from parsers
            remaining = think_parser.flush()
            if remaining:
                if remaining.type == ContentType.THINKING:
                    for event in sse.ensure_thinking_block():
                        yield event
                    yield sse.emit_thinking_delta(remaining.content)
                else:
                    for event in sse.ensure_text_block():
                        yield event
                    yield sse.emit_text_delta(remaining.content)

            for tool_use in heuristic_parser.flush():
                for event in sse.close_content_blocks():
                    yield event

                block_idx = sse.blocks.allocate_index()
                yield sse.content_block_start(
                    block_idx,
                    "tool_use",
                    id=tool_use["id"],
                    name=tool_use["name"],
                )
                yield sse.content_block_delta(
                    block_idx,
                    "input_json_delta",
                    json.dumps(tool_use["input"]),
                )
                yield sse.content_block_stop(block_idx)

            # Ensure at least one text block if no content/error occurred
            if not error_occurred and sse.blocks.text_index == -1 and not sse.blocks.tool_indices:
                for event in sse.ensure_text_block():
                    yield event
                yield sse.emit_text_delta(" ")

            # Close all blocks
            for event in sse.close_all_blocks():
                yield event

            # Send final events
            output_tokens = (
                usage_info.completion_tokens
                if usage_info and hasattr(usage_info, "completion_tokens")
                else sse.estimate_output_tokens()
            )
            yield sse.message_delta(map_stop_reason(finish_reason), output_tokens)
            yield sse.message_stop()
            yield sse.done()

            logger.debug(f"NIM_STREAM: {message_id} - completed")

    async def complete(self, request: Any) -> dict:
        """Make a non-streaming completion request."""
        await self._global_rate_limiter.wait_if_blocked()

        body = self._build_request_body(request, stream=False)
        logger.info(
            f"NIM_COMPLETE: model={body.get('model')} "
            f"msgs={len(body.get('messages', []))} "
            f"tools={len(body.get('tools', []))}"
        )

        try:
            response = await self._client.chat.completions.create(**body)
            return response.model_dump()
        except Exception as e:
            logger.error(f"NIM_ERROR: {type(e).__name__}: {e}")
            raise self._map_error(e)

    def _process_tool_call(self, tc: dict, sse: Any, request_id: str = None):
        """Process a single tool call delta and yield SSE events.

        Args:
            tc: Tool call delta info dict
            sse: SSEBuilder instance
            request_id: Request ID for logging (optional)
        """
        tc_index = tc.get("index", 0)
        if tc_index < 0:
            tc_index = len(sse.blocks.tool_indices)

        fn_delta = tc.get("function", {})
        if fn_delta.get("name") is not None:
            sse.blocks.tool_names[tc_index] = (
                sse.blocks.tool_names.get(tc_index, "") + fn_delta["name"]
            )

        if tc_index not in sse.blocks.tool_indices:
            name = sse.blocks.tool_names.get(tc_index, "")
            if name or tc.get("id"):
                tool_id = tc.get("id") or f"tool_{uuid.uuid4().hex}"
                yield sse.start_tool_block(tc_index, tool_id, name)
                sse.blocks.tool_started[tc_index] = True
        elif not sse.blocks.tool_started.get(tc_index) and sse.blocks.tool_names.get(
            tc_index
        ):
            tool_id = tc.get("id") or f"tool_{uuid.uuid4().hex}"
            name = sse.blocks.tool_names[tc_index]
            yield sse.start_tool_block(tc_index, tool_id, name)
            sse.blocks.tool_started[tc_index] = True

        args = fn_delta.get("arguments", "")
        if args:
            if not sse.blocks.tool_started.get(tc_index):
                tool_id = tc.get("id") or f"tool_{uuid.uuid4().hex}"
                name = sse.blocks.tool_names.get(tc_index, "tool_call") or "tool_call"

                yield sse.start_tool_block(tc_index, tool_id, name)
                sse.blocks.tool_started[tc_index] = True

            # INTERCEPTION: Force run_in_background=False for Task tool
            current_name = sse.blocks.tool_names.get(tc_index, "")
            if current_name == "Task":
                try:
                    args_json = json.loads(args)
                    if args_json.get("run_in_background") is not False:
                        if request_id:
                            logger.info(
                                f"NIM_INTERCEPT: {request_id} - "
                                f"forcing run_in_background=False for Task {tc.get('id', 'unknown')}"
                            )
                        args_json["run_in_background"] = False
                        args = json.dumps(args_json)
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning(
                        f"NIM_INTERCEPT: Failed to parse/modify Task args: {e}"
                    )

            yield sse.emit_tool_delta(tc_index, args)

    async def close(self):
        """Explicitly close the provider and release resources.

        This should be called during application shutdown.
        """
        if hasattr(self, '_client') and self._client:
            await self._client.close()
            logger.info("NvidiaNimProvider: client closed")
