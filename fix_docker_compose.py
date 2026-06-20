import re

with open('docker-compose.yml', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace finance
content = re.sub(r'traefik\.http\.routers\.finance\.rule=PathPrefix\([^\)]+\)', 
                 r'traefik.http.routers.finance.rule=PathPrefix(`/rut-tien`) || PathPrefix(`/nap-tien`) || PathPrefix(`/kiem-tien`) || PathPrefix(`/ma-qua-tang`) || PathPrefix(`/vi-tien`)', content)

# Replace notification
content = re.sub(r'traefik\.http\.routers\.notification\.rule=PathPrefix\([^\)]+\)', 
                 r'traefik.http.routers.notification.rule=PathPrefix(`/thong-bao`)', content)

# Replace ai
content = re.sub(r'traefik\.http\.routers\.ai\.rule=PathPrefix\([^\)]+\)', 
                 r'traefik.http.routers.ai.rule=PathPrefix(`/lich-su`) || PathPrefix(`/phan-hoi`) || PathPrefix(`/suy-luan`) || PathPrefix(`/nap-du-lieu`) || PathPrefix(`/tinh-chinh`) || PathPrefix(`/tro-chuyen`)', content)

# Replace collector
content = re.sub(r'traefik\.http\.routers\.collector\.rule=PathPrefix\([^\)]+\)', 
                 r'traefik.http.routers.collector.rule=PathPrefix(`/thu-thap`)', content)

# Replace editor
content = re.sub(r'traefik\.http\.routers\.editor\.rule=PathPrefix\([^\)]+\)', 
                 r'traefik.http.routers.editor.rule=PathPrefix(`/trinh-soan-thao`)', content)

# Replace authentication
content = re.sub(r'traefik\.http\.routers\.authentication\.rule=PathPrefix\([^\)]+\)', 
                 r'traefik.http.routers.authentication.rule=PathPrefix(`/xac-thuc`)', content)

# Replace management
content = re.sub(r'traefik\.http\.routers\.management\.rule=PathPrefix\([^\)]+\)', 
                 r'traefik.http.routers.management.rule=PathPrefix(`/giam-sat`) || PathPrefix(`/han-muc`) || PathPrefix(`/ho-so`) || PathPrefix(`/kiem-toan`) || PathPrefix(`/nguoi-dung`) || PathPrefix(`/quang-cao`) || PathPrefix(`/van-hanh`)', content)

# Replace realtime
content = re.sub(r'traefik\.http\.routers\.realtime\.rule=PathPrefix\([^\)]+\)', 
                 r'traefik.http.routers.realtime.rule=PathPrefix(`/ws`)', content)

# Replace messaging
content = re.sub(r'traefik\.http\.routers\.messaging\.rule=PathPrefix\([^\)]+\)', 
                 r'traefik.http.routers.messaging.rule=PathPrefix(`/tin-nhan`)', content)

# Replace content
content = re.sub(r'traefik\.http\.routers\.content\.rule=PathPrefix\([^\)]+\)', 
                 r'traefik.http.routers.content.rule=PathPrefix(`/ban-nhap`) || PathPrefix(`/cong-tac`) || PathPrefix(`/danh-dau`) || PathPrefix(`/danh-gia`) || PathPrefix(`/doc-hieu`) || PathPrefix(`/ghim`) || PathPrefix(`/ket-xuat`) || PathPrefix(`/kham-pha`) || PathPrefix(`/luu-tru`) || PathPrefix(`/phien-ban`) || PathPrefix(`/tai-len`) || PathPrefix(`/tai-lieu`) || PathPrefix(`/thu-vien`) || PathPrefix(`/xuat-ban`)', content)


with open('docker-compose.yml', 'w', encoding='utf-8') as f:
    f.write(content)

print("docker-compose.yml updated successfully!")
