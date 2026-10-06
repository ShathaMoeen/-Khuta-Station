import asyncio
from types import SimpleNamespace

from app.ai import GeminiProvider


class _Response:
    def __init__(self, body):
        self.body=body

    def raise_for_status(self):
        return None

    def json(self):
        return self.body


class _Client:
    def __init__(self, body):
        self.body=body
        self.calls=[]

    async def post(self, url, json):
        self.calls.append((url,json))
        return _Response(self.body)


def test_gemini_embedding_2_uses_distinct_document_and_query_prefixes(monkeypatch):
    async def verified(self, model, action):
        assert model=='gemini-embedding-2' and action=='embedContent'
        return {'supportedGenerationMethods':['embedContent']}

    monkeypatch.setattr(GeminiProvider,'verify_model',verified)
    provider=object.__new__(GeminiProvider)
    provider.settings=SimpleNamespace(embedding_provider='gemini',embedding_dimensions=1536,
        embedding_model='gemini-embedding-2')
    provider.client=_Client({'embeddings':[{'values':[0.25]*1536}]})

    document_vectors=asyncio.run(provider.embed(['exact controlled passage']))
    query_vectors=asyncio.run(provider.embed_query(['test query']))

    document_call,query_call=provider.client.calls
    assert len(document_vectors[0])==len(query_vectors[0])==1536
    assert document_call[0].endswith('/models/gemini-embedding-2:batchEmbedContents')
    assert document_call[1]['requests'][0]['output_dimensionality']==1536
    assert document_call[1]['requests'][0]['content']['parts'][0]['text']=='title: none | text: exact controlled passage'
    assert query_call[1]['requests'][0]['content']['parts'][0]['text']=='task: search result | query: test query'


def test_gemini_single_vector_probe_requests_1536_and_returns_actual_length(monkeypatch):
    async def verified(self, model, action):
        assert model=='gemini-embedding-2' and action=='embedContent'
        return {'supportedGenerationMethods':['embedContent']}

    monkeypatch.setattr(GeminiProvider,'verify_model',verified)
    provider=object.__new__(GeminiProvider)
    provider.settings=SimpleNamespace(embedding_model='gemini-embedding-2')
    provider.client=_Client({'embedding':{'values':[0.5]*1536}})

    dimension=asyncio.run(provider.probe_embedding('probe text'))

    url,body=provider.client.calls[0]
    assert dimension==1536
    assert url.endswith('/models/gemini-embedding-2:embedContent')
    assert body['output_dimensionality']==1536
