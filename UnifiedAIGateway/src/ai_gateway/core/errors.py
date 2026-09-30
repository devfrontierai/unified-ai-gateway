class GatewayError(Exception):
    """Base class for all Gateway exceptions."""
    pass

class AuthenticationError(GatewayError):
    pass

class AuthorizationError(GatewayError):
    pass

class ModelNotFoundError(GatewayError):
    pass

class ProviderUnavailableError(GatewayError):
    pass

class ProviderTimeoutError(GatewayError):
    pass

class ProviderRateLimitError(GatewayError):
    pass

class UnsupportedCapabilityError(GatewayError):
    pass

class RoutingError(GatewayError):
    pass

class PolicyDeniedError(GatewayError):
    pass

class GatewayConfigurationError(GatewayError):
    pass

class SecurityViolationError(GatewayError):
    pass
