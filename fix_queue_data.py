with open("docker-compose.yml", "r") as f:
    content = f.read()

content = content.replace("- queue_data:/var/lib/rabbitmq", "- rabbitmq_data:/var/lib/rabbitmq")
with open("docker-compose.yml", "w") as f:
    f.write(content)
