"""
Form Configuration Storage

SQLite-based persistence for form configurations.
"""

import logging
import json
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from app.models.form_config import (
    FormConfig,
    FormField,
    BusinessProfile,
    AgentConfig,
    FieldType,
    Industry,
    AgentTone,
    TTSVoice,
)

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path("./data/notera.db")


def init_form_database() -> None:
    """Initialize the SQLite database with form configuration tables."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Create form_configs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS form_configs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            business_name TEXT NOT NULL,
            business_industry TEXT DEFAULT 'other',
            business_description TEXT,
            business_phone TEXT,
            business_email TEXT,
            business_website TEXT,
            agent_name TEXT DEFAULT 'Alex',
            agent_tone TEXT DEFAULT 'professional',
            agent_voice TEXT DEFAULT 'nova',
            agent_custom_greeting TEXT,
            agent_custom_closing TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create form_fields table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS form_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_config_id TEXT NOT NULL,
            name TEXT NOT NULL,
            label TEXT NOT NULL,
            type TEXT DEFAULT 'text',
            description TEXT,
            required BOOLEAN DEFAULT 1,
            options TEXT,
            example TEXT,
            field_order INTEGER DEFAULT 0,
            FOREIGN KEY (form_config_id) REFERENCES form_configs(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_form_config_id ON form_fields(form_config_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_form_active ON form_configs(is_active)")
    
    conn.commit()
    conn.close()
    
    logger.info(f"Form database initialized at {DB_PATH}")


def _form_config_to_dict(config: FormConfig) -> Dict[str, Any]:
    """Convert FormConfig to database-friendly dict."""
    # Handle industry - could be enum or string
    industry = config.business.industry
    if hasattr(industry, 'value'):
        industry = industry.value
    elif industry is None:
        industry = "other"
    
    # Handle tone - could be enum or string
    tone = config.agent.tone
    if hasattr(tone, 'value'):
        tone = tone.value
    elif tone is None:
        tone = "professional"
    
    # Handle voice - could be enum or string
    voice = config.agent.voice
    if hasattr(voice, 'value'):
        voice = voice.value
    elif voice is None:
        voice = "nova"
    
    return {
        "id": config.id,
        "name": config.name,
        "business_name": config.business.name,
        "business_industry": industry,
        "business_description": config.business.description,
        "business_phone": getattr(config.business, 'phone', None),
        "business_email": getattr(config.business, 'email', None),
        "business_website": getattr(config.business, 'website', None),
        "agent_name": config.agent.name,
        "agent_tone": tone,
        "agent_voice": voice,
        "agent_custom_greeting": config.agent.custom_greeting,
        "agent_custom_closing": config.agent.custom_closing,
        "is_active": config.is_active,
        "created_at": config.created_at.isoformat() if config.created_at else datetime.now().isoformat(),
        "updated_at": config.updated_at.isoformat() if config.updated_at else datetime.now().isoformat(),
    }


def _row_to_form_config(row: sqlite3.Row, fields: List[sqlite3.Row]) -> FormConfig:
    """Convert database row to FormConfig."""
    # Build business profile
    business = BusinessProfile(
        name=row["business_name"],
        industry=Industry(row["business_industry"]) if row["business_industry"] else Industry.OTHER,
        description=row["business_description"],
        website=row["business_website"],
    )
    
    # Build agent config
    agent = AgentConfig(
        name=row["agent_name"] or "Alex",
        tone=AgentTone(row["agent_tone"]) if row["agent_tone"] else AgentTone.PROFESSIONAL,
        voice=TTSVoice(row["agent_voice"]) if row["agent_voice"] else TTSVoice.NOVA,
        custom_greeting=row["agent_custom_greeting"],
        custom_closing=row["agent_custom_closing"],
    )
    
    # Build fields
    form_fields = []
    for f in fields:
        options = json.loads(f["options"]) if f["options"] else None
        form_fields.append(FormField(
            name=f["name"],
            label=f["label"],
            type=FieldType(f["type"]) if f["type"] else FieldType.TEXT,
            description=f["description"],
            required=bool(f["required"]),
            options=options,
            example=f["example"],
            order=f["field_order"] or 0,
        ))
    
    # Sort fields by order
    form_fields.sort(key=lambda x: x.order)
    
    return FormConfig(
        id=row["id"],
        name=row["name"],
        business=business,
        agent=agent,
        fields=form_fields,
        is_active=bool(row["is_active"]),
        created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
        updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(),
    )


def save_form_config(config: FormConfig) -> bool:
    """
    Save or update a form configuration.
    
    Args:
        config: FormConfig to save
        
    Returns:
        True if successful
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        data = _form_config_to_dict(config)
        
        # Check if exists
        cursor.execute("SELECT id FROM form_configs WHERE id = ?", (config.id,))
        exists = cursor.fetchone() is not None
        
        if exists:
            # Update
            cursor.execute("""
                UPDATE form_configs SET
                    name = ?, business_name = ?, business_industry = ?,
                    business_description = ?, business_phone = ?, business_email = ?,
                    business_website = ?, agent_name = ?, agent_tone = ?,
                    agent_voice = ?, agent_custom_greeting = ?, agent_custom_closing = ?,
                    is_active = ?, updated_at = ?
                WHERE id = ?
            """, (
                data["name"], data["business_name"], data["business_industry"],
                data["business_description"], data["business_phone"], data["business_email"],
                data["business_website"], data["agent_name"], data["agent_tone"],
                data["agent_voice"], data["agent_custom_greeting"], data["agent_custom_closing"],
                data["is_active"], datetime.now().isoformat(), config.id
            ))
            
            # Delete existing fields
            cursor.execute("DELETE FROM form_fields WHERE form_config_id = ?", (config.id,))
        else:
            # Insert
            cursor.execute("""
                INSERT INTO form_configs (
                    id, name, business_name, business_industry, business_description,
                    business_phone, business_email, business_website, agent_name,
                    agent_tone, agent_voice, agent_custom_greeting, agent_custom_closing,
                    is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config.id, data["name"], data["business_name"], data["business_industry"],
                data["business_description"], data["business_phone"], data["business_email"],
                data["business_website"], data["agent_name"], data["agent_tone"],
                data["agent_voice"], data["agent_custom_greeting"], data["agent_custom_closing"],
                data["is_active"], data["created_at"], data["updated_at"]
            ))
        
        # Insert fields
        for field in config.fields:
            options_json = json.dumps(field.options) if field.options else None
            # Handle field.type - could be enum or string
            field_type = field.type.value if hasattr(field.type, 'value') else field.type
            cursor.execute("""
                INSERT INTO form_fields (
                    form_config_id, name, label, type, description,
                    required, options, example, field_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config.id, field.name, field.label, field_type,
                field.description, field.required, options_json,
                field.example, field.order
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved form config: {config.id} ({config.name})")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save form config: {e}")
        return False


def load_form_config(config_id: str) -> Optional[FormConfig]:
    """
    Load a form configuration by ID.
    
    Args:
        config_id: Form configuration ID
        
    Returns:
        FormConfig or None if not found
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get config
        cursor.execute("SELECT * FROM form_configs WHERE id = ?", (config_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # Get fields
        cursor.execute(
            "SELECT * FROM form_fields WHERE form_config_id = ? ORDER BY field_order",
            (config_id,)
        )
        fields = cursor.fetchall()
        
        conn.close()
        
        return _row_to_form_config(row, fields)
        
    except Exception as e:
        logger.error(f"Failed to load form config: {e}")
        return None


def list_form_configs(
    active_only: bool = True,
    limit: int = 50,
    offset: int = 0
) -> List[FormConfig]:
    """
    List form configurations.
    
    Args:
        active_only: Only return active configs
        limit: Maximum results
        offset: Pagination offset
        
    Returns:
        List of FormConfig objects
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM form_configs"
        params = []
        
        if active_only:
            query += " WHERE is_active = 1"
        
        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        configs = []
        for row in rows:
            # Get fields for each config
            cursor.execute(
                "SELECT * FROM form_fields WHERE form_config_id = ? ORDER BY field_order",
                (row["id"],)
            )
            fields = cursor.fetchall()
            configs.append(_row_to_form_config(row, fields))
        
        conn.close()
        return configs
        
    except Exception as e:
        logger.error(f"Failed to list form configs: {e}")
        return []


def delete_form_config(config_id: str) -> bool:
    """
    Delete a form configuration.
    
    Args:
        config_id: Form configuration ID
        
    Returns:
        True if successful
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Delete fields first (foreign key)
        cursor.execute("DELETE FROM form_fields WHERE form_config_id = ?", (config_id,))
        
        # Delete config
        cursor.execute("DELETE FROM form_configs WHERE id = ?", (config_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted form config: {config_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete form config: {e}")
        return False


def count_form_configs(active_only: bool = True) -> int:
    """Count form configurations."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) FROM form_configs"
        if active_only:
            query += " WHERE is_active = 1"
        
        cursor.execute(query)
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
        
    except Exception as e:
        logger.error(f"Failed to count form configs: {e}")
        return 0
