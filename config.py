import os
from dataclasses import dataclass
from typing import Optional
import streamlit as st

@dataclass
class Config:
    """Configuration class for F1 Agent application"""
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_API_VERSION: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str
    
    # Application Configuration
    APP_TITLE: str = "F1 Racer AI Agent"
    APP_DESCRIPTION: str = "AI-powered Formula 1 racer social media agent"
    DEBUG_MODE: bool = False
    
    # Authentication Configuration
    SESSION_TIMEOUT_MINUTES: int = 60
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_MINUTES: int = 15
    
    # Agent Configuration
    DEFAULT_RACER_NAME: str = "Lightning McQueen"
    DEFAULT_TEAM_NAME: str = "Rusteze Racing"
    DEFAULT_CIRCUIT: str = "Nurburgring"
    DEFAULT_RACE: str = "German Grand Prix"
    
    # LLM Configuration
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 500
    LLM_TIMEOUT_SECONDS: int = 30
    
    # UI Configuration
    SIDEBAR_WIDTH: int = 300
    MAX_INTERACTION_HISTORY: int = 50
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables"""
        
        # Required Azure OpenAI configuration
        azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        azure_api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        azure_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
        
        # Validate required configuration
        if not azure_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
        if not azure_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY environment variable is required")
        
        return cls(
            # Azure OpenAI
            AZURE_OPENAI_ENDPOINT=azure_endpoint,
            AZURE_OPENAI_API_KEY=azure_api_key,
            AZURE_OPENAI_API_VERSION=azure_api_version,
            AZURE_OPENAI_DEPLOYMENT_NAME=azure_deployment,
            
            # Application settings
            APP_TITLE=os.environ.get("APP_TITLE", "F1 Racer AI Agent"),
            APP_DESCRIPTION=os.environ.get("APP_DESCRIPTION", "AI-powered Formula 1 racer social media agent"),
            DEBUG_MODE=os.environ.get("DEBUG_MODE", "false").lower() == "true",
            
            # Authentication
            SESSION_TIMEOUT_MINUTES=int(os.environ.get("SESSION_TIMEOUT_MINUTES", "60")),
            MAX_LOGIN_ATTEMPTS=int(os.environ.get("MAX_LOGIN_ATTEMPTS", "5")),
            LOGIN_RATE_LIMIT_MINUTES=int(os.environ.get("LOGIN_RATE_LIMIT_MINUTES", "15")),
            
            # Agent defaults
            DEFAULT_RACER_NAME=os.environ.get("DEFAULT_RACER_NAME", "Lightning McQueen"),
            DEFAULT_TEAM_NAME=os.environ.get("DEFAULT_TEAM_NAME", "Rusteze Racing"),
            DEFAULT_CIRCUIT=os.environ.get("DEFAULT_CIRCUIT", "Nurburgring"),
            DEFAULT_RACE=os.environ.get("DEFAULT_RACE", "German Grand Prix"),
            
            # LLM settings
            LLM_TEMPERATURE=float(os.environ.get("LLM_TEMPERATURE", "0.7")),
            LLM_MAX_TOKENS=int(os.environ.get("LLM_MAX_TOKENS", "500")),
            LLM_TIMEOUT_SECONDS=int(os.environ.get("LLM_TIMEOUT_SECONDS", "30")),
            
            # UI settings
            SIDEBAR_WIDTH=int(os.environ.get("SIDEBAR_WIDTH", "300")),
            MAX_INTERACTION_HISTORY=int(os.environ.get("MAX_INTERACTION_HISTORY", "50"))
        )
    
    def validate(self) -> bool:
        """Validate configuration"""
        required_fields = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_API_VERSION",
            "AZURE_OPENAI_DEPLOYMENT_NAME"
        ]
        
        for field in required_fields:
            if not getattr(self, field):
                return False
        
        # Validate numeric ranges
        if not (0.0 <= self.LLM_TEMPERATURE <= 2.0):
            return False
        
        if not (50 <= self.LLM_MAX_TOKENS <= 4000):
            return False
        
        if not (5 <= self.LLM_TIMEOUT_SECONDS <= 300):
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }
    
    def get_safe_dict(self) -> dict:
        """Get configuration dictionary with sensitive data masked"""
        config_dict = self.to_dict()
        
        # Mask sensitive information
        sensitive_fields = ["AZURE_OPENAI_API_KEY"]
        
        for field in sensitive_fields:
            if field in config_dict and config_dict[field]:
                config_dict[field] = "*" * 8 + config_dict[field][-4:]
        
        return config_dict

# Global configuration instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Get global configuration instance"""
    global _config
    
    if _config is None:
        try:
            _config = Config.from_env()
            if not _config.validate():
                raise ValueError("Configuration validation failed")
        except Exception as e:
            st.error(f"Configuration error: {e}")
            st.info("""
            Please ensure the following environment variables are set:
            - AZURE_OPENAI_ENDPOINT
            - AZURE_OPENAI_API_KEY
            - AZURE_OPENAI_API_VERSION (optional)
            - AZURE_OPENAI_DEPLOYMENT_NAME (optional)
            """)
            st.stop()
    
    return _config

def reload_config():
    """Reload configuration from environment"""
    global _config
    _config = None
    return get_config()

def is_production() -> bool:
    """Check if running in production environment"""
    return os.environ.get("ENVIRONMENT", "development").lower() == "production"

def get_app_version() -> str:
    """Get application version"""
    return os.environ.get("APP_VERSION", "1.0.0")

def get_deployment_info() -> dict:
    """Get deployment information"""
    return {
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "version": get_app_version(),
        "deployed_at": os.environ.get("DEPLOYMENT_TIMESTAMP", "unknown"),
        "commit_hash": os.environ.get("COMMIT_HASH", "unknown"),
        "is_production": is_production()
    }

# Environment validation
def validate_environment() -> tuple[bool, list]:
    """Validate environment configuration"""
    errors = []
    
    # Check required environment variables
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY"
    ]
    
    for var in required_vars:
        if not os.environ.get(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Check Azure OpenAI endpoint format
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    if endpoint and not endpoint.startswith("https://"):
        errors.append("AZURE_OPENAI_ENDPOINT must start with https://")
    
    # Check API version format
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION")
    if api_version and not api_version.startswith("20"):
        errors.append("AZURE_OPENAI_API_VERSION should be in format YYYY-MM-DD-preview")
    
    return len(errors) == 0, errors

# Development utilities
def get_env_info() -> dict:
    """Get environment information for debugging"""
    return {
        "python_version": os.sys.version,
        "environment_vars": {
            key: value if "API_KEY" not in key and "PASSWORD" not in key else "*" * 8
            for key, value in os.environ.items()
            if key.startswith(("AZURE_", "APP_", "DEBUG", "ENVIRONMENT"))
        },
        "config_valid": _config is not None and _config.validate() if _config else False,
        "streamlit_version": st.__version__
    }

# Configuration for different environments
def get_environment_config() -> dict:
    """Get environment-specific configuration"""
    env = os.environ.get("ENVIRONMENT", "development").lower()
    
    base_config = {
        "development": {
            "debug": True,
            "log_level": "DEBUG",
            "session_timeout": 120,  # 2 hours
            "rate_limit_enabled": False
        },
        "staging": {
            "debug": False,
            "log_level": "INFO",
            "session_timeout": 60,  # 1 hour
            "rate_limit_enabled": True
        },
        "production": {
            "debug": False,
            "log_level": "WARNING",
            "session_timeout": 30,  # 30 minutes
            "rate_limit_enabled": True
        }
    }
    
    return base_config.get(env, base_config["development"])

# Health check configuration
def health_check() -> dict:
    """Perform health check on configuration and dependencies"""
    health = {
        "status": "healthy",
        "checks": {},
        "timestamp": os.time.time()
    }
    
    # Check configuration
    try:
        config = get_config()
        health["checks"]["config"] = "ok"
    except Exception as e:
        health["checks"]["config"] = f"error: {e}"
        health["status"] = "unhealthy"
    
    # Check environment variables
    is_valid, errors = validate_environment()
    if is_valid:
        health["checks"]["environment"] = "ok"
    else:
        health["checks"]["environment"] = f"errors: {errors}"
        health["status"] = "unhealthy"
    
    # Check Azure OpenAI connectivity (basic)
    try:
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        if endpoint:
            health["checks"]["azure_openai_endpoint"] = "configured"
        else:
            health["checks"]["azure_openai_endpoint"] = "not configured"
    except Exception as e:
        health["checks"]["azure_openai_endpoint"] = f"error: {e}"
    
    return health
