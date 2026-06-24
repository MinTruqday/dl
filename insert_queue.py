with open("docker-compose.yml", "r") as f:
    lines = f.readlines()

new_svc = """  queue:
    build:
      context: ./backend
      dockerfile: ./queue/Dockerfile
    container_name: doclib_queue
    restart: always
    ports:
      - "8802:8802"
    env_file:
      - .env
    depends_on:
      - rabbitmq
    networks:
      - doclib_network

"""

for i, line in enumerate(lines):
    if line.startswith("networks:"):
        lines.insert(i, new_svc)
        break

with open("docker-compose.yml", "w") as f:
    f.writelines(lines)
