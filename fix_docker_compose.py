import os
import yaml

with open("docker-compose.yml", "r") as f:
    content = f.read()

# Since pyyaml is not available, I'll just append the queue service to the end, but docker-compose.yml has "volumes:" and "networks:" at the bottom!
