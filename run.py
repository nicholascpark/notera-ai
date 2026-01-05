#!/usr/bin/env python3
"""Notera AI - Run Script"""

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                        Notera AI                              ║
║              Conversational Form Builder                      ║
╚═══════════════════════════════════════════════════════════════╝

Starting server...
  - Host: {settings.host}
  - Port: {settings.port}
  - Environment: {settings.environment}
  - Debug: {settings.debug}
  
API Documentation: http://{settings.host}:{settings.port}/docs
""")
    
    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=not settings.is_production,
        log_level="debug" if settings.debug else "info"
    )
