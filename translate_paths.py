import os
import re

db_api_file = "backend/database/src/api/mongo.py"
queue_api_file = "backend/queue/src/api/queue_api.py"
queue_main_file = "backend/queue/src/main.py"

# Database service changes
with open(db_api_file, 'r') as f:
    db_content = f.read()

db_content = db_content.replace('prefix="/mongo"', 'prefix="/co-so-du-lieu"')
db_content = db_content.replace('"/find"', '"/tim-kiem"')
db_content = db_content.replace('"/find_one"', '"/tim-mot"')
db_content = db_content.replace('"/insert_one"', '"/them-mot"')
db_content = db_content.replace('"/update_one"', '"/cap-nhat-mot"')
db_content = db_content.replace('"/update_many"', '"/cap-nhat-nhieu"')
db_content = db_content.replace('"/delete_one"', '"/xoa-mot"')
db_content = db_content.replace('"/delete_many"', '"/xoa-nhieu"')
db_content = db_content.replace('"/aggregate"', '"/tong-hop"')
db_content = db_content.replace('"/count_documents"', '"/dem-tai-lieu"')

with open(db_api_file, 'w') as f:
    f.write(db_content)

# Queue service changes
with open(queue_api_file, 'r') as f:
    q_content = f.read()

q_content = q_content.replace('"/publish"', '"/xuat-ban"')
q_content = q_content.replace('"/consume/{queue_name}"', '"/tieu-thu/{queue_name}"')
with open(queue_api_file, 'w') as f:
    f.write(q_content)

with open(queue_main_file, 'r') as f:
    qm_content = f.read()

qm_content = qm_content.replace('prefix="/queue"', 'prefix="/hang-doi"')
with open(queue_main_file, 'w') as f:
    f.write(qm_content)

# Update client files across all services
for root, dirs, files in os.walk("backend"):
    for file in files:
        if file == "mongo.py":
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
            
            content = content.replace('/mongo"', '/co-so-du-lieu"')
            content = content.replace('"/find"', '"/tim-kiem"')
            content = content.replace('"/find_one"', '"/tim-mot"')
            content = content.replace('"/insert_one"', '"/them-mot"')
            content = content.replace('"/update_one"', '"/cap-nhat-mot"')
            content = content.replace('"/update_many"', '"/cap-nhat-nhieu"')
            content = content.replace('"/delete_one"', '"/xoa-mot"')
            content = content.replace('"/delete_many"', '"/xoa-nhieu"')
            content = content.replace('"/aggregate"', '"/tong-hop"')
            content = content.replace('"/count_documents"', '"/dem-tai-lieu"')

            with open(filepath, 'w') as f:
                f.write(content)
        
        elif file == "mq.py":
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
            
            content = content.replace('/queue"', '/hang-doi"')
            content = content.replace('"/publish"', '"/xuat-ban"')
            content = content.replace('"/consume/', '"/tieu-thu/')

            with open(filepath, 'w') as f:
                f.write(content)

