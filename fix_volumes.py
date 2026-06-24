with open("docker-compose.yml", "r") as f:
    content = f.read()

content = content.replace("  redis_data:", "volumes:\n  mongodb_data:\n  redis_data:")
with open("docker-compose.yml", "w") as f:
    f.write(content)
