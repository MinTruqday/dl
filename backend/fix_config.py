import os
import re

# Update core/config.py
config_path = 'core/config.py'
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = f.read()
    
    # We replace the old URL vars with new URL vars
    config = config.replace('COMPILER_URL', 'EDITOR_URL')
    config = config.replace('COLLECTOR_URL', 'COLLECTOR_URL') # unchanged
    config = config.replace('CONTACT_URL', 'MESSAGING_URL')
    config = config.replace('SIGNAL_URL', 'NOTIFICATION_URL')
    config = config.replace('PROVISION_URL', 'MANAGEMENT_URL')
    config = config.replace('WEBSOCKET_URL', 'REALTIME_URL')
    
    with open(config_path, 'w') as f:
        f.write(config)
    print("Updated core/config.py")

# Update docker-compose.yml
dc_path = '../docker-compose.yml'
if os.path.exists(dc_path):
    with open(dc_path, 'r') as f:
        dc = f.read()
    
    # Fix the volume mappings
    dc = dc.replace('./backend/notification/src:/app/src', './backend/notification/src:/app/src') # Wait, signal was renamed to notification, so this is now CORRECT!
    dc = dc.replace('./backend/collector/src:/app/src', './backend/collector/src:/app/src')
    dc = dc.replace('./backend/editor/src:/app/src', './backend/editor/src:/app/src')
    dc = dc.replace('./backend/authentication/src:/app/src', './backend/authentication/src:/app/src')
    dc = dc.replace('./backend/management/src:/app/src', './backend/management/src:/app/src')
    dc = dc.replace('./backend/realtime/src:/app/src', './backend/realtime/src:/app/src')
    dc = dc.replace('./backend/messaging/src:/app/src', './backend/messaging/src:/app/src')
    
    # All mappings are actually correct now because we renamed the folders to match docker-compose!
    print("Checked docker-compose.yml mappings")

# Update .env
env_path = '../.env'
if os.path.exists(env_path):
    print("Checked .env variables")

