import yaml

ingress_file = "k8s/ingress/ingress.yaml"

# Load the ground truth prefixes mapped to services
service_map = {
    "finance-service": ["/kiem-tien", "/ma-qua-tang", "/nap-tien", "/rut-tien", "/vi-tien"],
    "agentic-ai-service": ["/lich-su", "/phan-hoi", "/suy-luan", "/nap-du-lieu", "/tinh-chinh", "/tro-chuyen"],
    "management-service": ["/giam-sat", "/han-muc", "/ho-so", "/kiem-toan", "/nguoi-dung", "/quang-cao", "/van-hanh"],
    "content-service": ["/ban-nhap", "/cong-tac", "/danh-dau", "/danh-gia", "/doc-hieu", "/ghim", "/ket-xuat", "/kham-pha", "/luu-tru", "/phien-ban", "/tai-len", "/tai-lieu", "/thu-vien", "/xuat-ban"],
    "messaging-service": ["/tin-nhan"],
    "authentication-service": ["/xac-thuc"], # /xac-thuc covers /xac-thuc/khoa-bao-mat automatically with (/|$)
    "editor-service": ["/trinh-soan-thao"],
    "notification-service": ["/thong-bao"],
    "collector-service": ["/thu-thap"],
    "realtime-service": ["/ws"]
}

# we need to build the new paths list
new_paths = []

for svc, prefixes in service_map.items():
    for prefix in prefixes:
        # e.g. /kiem-tien(/|$)(.*)
        path_str = f"{prefix}(/|$)(.*)"
        new_paths.append({
            "path": path_str,
            "pathType": "ImplementationSpecific",
            "backend": {
                "service": {
                    "name": svc,
                    "port": {"number": 80}
                }
            }
        })

# Add frontend at the end
new_paths.append({
    "path": "/(.*)",
    "pathType": "ImplementationSpecific",
    "backend": {
        "service": {
            "name": "frontend-service",
            "port": {"number": 80}
        }
    }
})

with open(ingress_file, 'r') as f:
    data = yaml.safe_load(f)

# Update the paths
data['spec']['rules'][0]['http']['paths'] = new_paths

with open(ingress_file, 'w') as f:
    yaml.dump(data, f, sort_keys=False, default_flow_style=False)

print("k8s/ingress/ingress.yaml updated.")
