"""Verify configured Gemini models and the real embedding dimension without database writes."""
from __future__ import annotations

import asyncio
import json
from urllib.parse import quote

from app.ai import GeminiProvider
from app.core.config import get_settings


async def main() -> None:
    settings=get_settings()
    if settings.llm_provider!='gemini' or settings.embedding_provider!='gemini':
        raise SystemExit('Gemini verification blocked: set both LLM_PROVIDER and EMBEDDING_PROVIDER to gemini.')
    if not settings.gemini_api_key:
        raise SystemExit('Gemini verification blocked: GEMINI_API_KEY is missing.')
    if not settings.llm_model or not settings.embedding_model:
        raise SystemExit('Gemini verification blocked: set LLM_MODEL and EMBEDDING_MODEL.')
    provider=GeminiProvider()
    try:
        llm=await provider.verify_model(settings.llm_model,'generateContent')
        model=quote(settings.llm_model.removeprefix('models/'),safe='-')
        response=await provider.client.post(f'{provider.API_ROOT}/models/{model}:generateContent',json={
            'contents':[{'role':'user','parts':[{'text':'Reply with the JSON object {"ok":true}.'}]}],
            'generationConfig':{'temperature':0,'maxOutputTokens':16,'responseMimeType':'application/json'}})
        response.raise_for_status()
        llm_ok=bool(response.json().get('candidates'))
        dimension=await provider.probe_embedding('KHUTA embedding dimension verification.')
        print(json.dumps({'gemini_key_request':'passed','llm_model':settings.llm_model,
            'llm_model_available':'generateContent' in (llm.get('supportedGenerationMethods') or []),
            'llm_probe':'passed' if llm_ok else 'failed','embedding_model':settings.embedding_model,
            'embedding_model_available':True,'actual_embedding_dimension':dimension,
            'database_dimension':1536,'dimension_compatible':dimension==1536},ensure_ascii=False))
        if not llm_ok: raise SystemExit('Gemini generation probe returned no candidate.')
        if dimension!=1536:
            raise SystemExit('Gemini embedding dimension is incompatible; no database insert was attempted.')
    finally:
        await provider.client.aclose()


if __name__=='__main__':
    asyncio.run(main())
