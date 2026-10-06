class KhutaError(Exception):
    status_code = 400
    code = 'khuta_error'


class NotFoundError(KhutaError):
    status_code = 404
    code = 'not_found'


class VisitorNotFoundError(NotFoundError):
    code = 'visitor_not_found'


class StationNotFoundError(NotFoundError):
    code = 'station_not_found'


class GovernanceEscalationError(KhutaError):
    status_code = 422
    code = 'governance_escalation'


class AIProviderError(KhutaError):
    status_code = 502
    code = 'ai_provider_error'


class GeminiRateLimitError(AIProviderError):
    code = 'gemini_rate_limited'


class CitationValidationError(KhutaError):
    status_code = 422
    code = 'citation_validation_error'

