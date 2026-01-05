"""Persistence service for conversation history and form configurations."""
from .database import (
    init_database, 
    save_conversation, 
    load_conversation,
    list_conversations,
    delete_conversation
)
from .form_storage import (
    init_form_database,
    save_form_config,
    load_form_config,
    list_form_configs,
    delete_form_config,
    count_form_configs,
)

__all__ = [
    # Conversation persistence
    "init_database",
    "save_conversation",
    "load_conversation", 
    "list_conversations",
    "delete_conversation",
    # Form config persistence
    "init_form_database",
    "save_form_config",
    "load_form_config",
    "list_form_configs",
    "delete_form_config",
    "count_form_configs",
]
