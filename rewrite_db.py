import os
import re

for root, dirs, files in os.walk("backend"):
    if "database.py" in files and "infrastructure" in root:
        fpath = os.path.join(root, "database.py")
        with open(fpath, "r") as f:
            c = f.read()

        # We will replace everything from `async def init_db():` to the end of the file.
        # But wait, there are some functions below like `setup_indexes()`.
        
        # Let's fix the specific blocks.
        # Block 1: The messy MongoDB block
        c = re.sub(r'    try:\n        pass\n    except Exception as e:\n        pass\n.*?(?=    database\.redis =)', '', c, flags=re.DOTALL)
        
        # Block 2: The RabbitMQ block
        c = re.sub(r'    for i in range\(max_retries\):\n        try:\n.*?    except Exception as e:\n', 
r'''    for i in range(max_retries):
        try:
            database.rabbitmq = await aio_pika.connect_robust(rabbitmq_uri)
            logger.info("Kết nối hàng đợi tin nhắn nền ổn định")
            break
        except Exception as e:
''', c, flags=re.DOTALL)

        with open(fpath, "w") as f:
            f.write(c)
