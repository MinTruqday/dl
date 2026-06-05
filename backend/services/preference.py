from core.database import db_client
from fastapi import HTTPException
from datetime import datetime, timezone
from loguru import logger

class PreferenceService:

    @staticmethod
    async def get_preferences(current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        prefs = await db['reading_preferences'].find_one({'user_id': str(current_user.id)})
        if not prefs:
            return {'theme': 'light', 'font_size': 16, 'line_height': 1.8, 'font_family': 'Inter', 'letter_spacing': 0, 'is_dyslexic_mode': False}
        return {'theme': prefs.get('theme', 'light'), 'font_size': prefs.get('font_size', 16), 'line_height': prefs.get('line_height', 1.8), 'font_family': prefs.get('font_family', 'Inter'), 'letter_spacing': prefs.get('letter_spacing', 0), 'is_dyslexic_mode': prefs.get('is_dyslexic_mode', False)}

    @staticmethod
    async def update_preferences(data: dict, current_user, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        existing = await db['reading_preferences'].find_one({'user_id': str(current_user.id)})
        if not existing:
            existing = {}
        allowed_themes = ['light', 'dark', 'gray', 'sepia']
        theme = data.get('theme', existing.get('theme', 'light'))
        if theme not in allowed_themes:
            theme = 'light'
        allowed_fonts = ['Inter', 'Roboto', 'Outfit', 'Noto Sans', 'Source Sans Pro']
        font = data.get('font_family', existing.get('font_family', 'Inter'))
        if font not in allowed_fonts:
            font = 'Inter'
        update_data = {'theme': theme, 'font_family': font, 'font_size': max(12, min(28, data.get('font_size', existing.get('font_size', 16)))), 'line_height': max(1.2, min(3.0, data.get('line_height', existing.get('line_height', 1.8)))), 'letter_spacing': max(-0.5, min(2.0, data.get('letter_spacing', existing.get('letter_spacing', 0)))), 'is_dyslexic_mode': data.get('is_dyslexic_mode', existing.get('is_dyslexic_mode', False)), 'updated_at': datetime.now(timezone.utc)}
        await db['reading_preferences'].update_one({'user_id': str(current_user.id)}, {'$set': update_data}, upsert=True)
        logger.info(f'Preference: Reading preferences updated for {current_user.id}')
        return {'message': 'Đã cập nhật tùy chỉnh giao diện đọc.'}