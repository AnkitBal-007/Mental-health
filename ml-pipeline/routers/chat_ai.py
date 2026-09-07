"""
FastAPI Router for AI Chatbot conversational interactions.
Endpoint: POST /chat/respond
"""

import logging
from fastapi import APIRouter, HTTPException, status

from schemas.chat import ChatRequest, ChatResponse
from services.gemini_chat import gemini_chat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["AI Chatbot"])


@router.post(
    "/respond",
    response_model=ChatResponse,
    summary="Generate empathetic conversational AI reply",
    description="Uses Google Gemini to generate a warm, trauma-informed response in English or Hindi while monitoring for crisis indicators.",
)
async def generate_chat_response(req: ChatRequest):
    """
    Takes the current user message, optional conversation history, and mood metadata,
    and returns a tailored, compassionate response from Saheli.
    """
    try:
        reply, is_crisis, model_used = await gemini_chat_service.generate_reply(
            message=req.message,
            history=req.history,
            language=req.language,
            sentiment_label=req.sentiment_label,
            emotion_label=req.emotion_label,
        )

        return ChatResponse(
            reply=reply,
            crisis_flag=is_crisis,
            language=req.language,
            model_used=model_used,
        )

    except Exception as e:
        logger.error("Error in /chat/respond: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate chat response: {str(e)}",
        )
