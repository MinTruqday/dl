import yaml

filepath = "docker-compose.yml"

with open(filepath, "r") as f:
    data = yaml.safe_load(f)

services_to_remove = ["doclib_cache", "database", "queue"]
removed = []

for svc in services_to_remove:
    if svc in data.get("services", {}):
        del data["services"][svc]
        removed.append(svc)

# Also remove from depends_on
for svc_name, svc_data in data.get("services", {}).items():
    if "depends_on" in svc_data:
        depends_on = svc_data["depends_on"]
        if isinstance(depends_on, list):
            new_depends = [dep for dep in depends_on if dep not in services_to_remove]
            if not new_depends:
                del svc_data["depends_on"]
            else:
                svc_data["depends_on"] = new_depends
        elif isinstance(depends_on, dict):
            new_depends = {k: v for k, v in depends_on.items() if k not in services_to_remove}
            if not new_depends:
                del svc_data["depends_on"]
            else:
                svc_data["depends_on"] = new_depends

class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)

with open(filepath, "w") as f:
    yaml.dump(data, f, Dumper=MyDumper, default_flow_style=False, sort_keys=False)

print(f"Removed from docker-compose.yml: {removed}")
