ingress_file = "k8s/ingress/ingress.yaml"

service_map = {
    "finance-service": ["/kiem-tien", "/ma-qua-tang", "/nap-tien", "/rut-tien", "/vi-tien"],
    "agentic-ai-service": ["/lich-su", "/phan-hoi", "/suy-luan", "/nap-du-lieu", "/tinh-chinh", "/tro-chuyen"],
    "management-service": ["/giam-sat", "/han-muc", "/ho-so", "/kiem-toan", "/nguoi-dung", "/quang-cao", "/van-hanh"],
    "content-service": ["/ban-nhap", "/cong-tac", "/danh-dau", "/danh-gia", "/doc-hieu", "/ghim", "/ket-xuat", "/kham-pha", "/luu-tru", "/phien-ban", "/tai-len", "/tai-lieu", "/thu-vien", "/xuat-ban"],
    "messaging-service": ["/tin-nhan"],
    "authentication-service": ["/xac-thuc"], 
    "editor-service": ["/trinh-soan-thao"],
    "notification-service": ["/thong-bao"],
    "collector-service": ["/thu-thap"],
    "realtime-service": ["/ws"]
}

lines = []
lines.append("apiVersion: networking.k8s.io/v1")
lines.append("kind: Ingress")
lines.append("metadata:")
lines.append("  name: doclib-ingress")
lines.append("  namespace: doclib-production")
lines.append("  annotations:")
lines.append("    nginx.ingress.kubernetes.io/use-regex: \"true\"")
lines.append("    nginx.ingress.kubernetes.io/rewrite-target: /$2")
lines.append("spec:")
lines.append("  rules:")
lines.append("  - http:")
lines.append("      paths:")

for svc, prefixes in service_map.items():
    for prefix in prefixes:
        lines.append(f"      - path: {prefix}(/|$)(.*)")
        lines.append( "        pathType: ImplementationSpecific")
        lines.append( "        backend:")
        lines.append( "          service:")
        lines.append(f"            name: {svc}")
        lines.append( "            port:")
        lines.append( "              number: 80")

lines.append("      # Frontend default route")
lines.append("      - path: /(.*)")
lines.append("        pathType: ImplementationSpecific")
lines.append("        backend:")
lines.append("          service:")
lines.append("            name: frontend-service")
lines.append("            port:")
lines.append("              number: 80")

with open(ingress_file, "w") as f:
    f.write("\n".join(lines) + "\n")

print("k8s/ingress/ingress.yaml generated.")
