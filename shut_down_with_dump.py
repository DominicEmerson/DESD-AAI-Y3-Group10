import subprocess
import os

CONTAINER = "desd-aai-y3-group10-database-1"   # <- correct Postgres container

print("Dumping PostgreSQL database inside container …")
subprocess.run([
    "docker", "exec", CONTAINER,
    "pg_dump", "-U", "user", "-d", "insurance_ai",
    "--encoding=UTF8", "--format=plain", "-f", "/tmp/insurance_ai_dump.sql"
], check=True)

output_path = os.path.join("init", "insurance_ai_dump.sql")
print(f"Copying dump file to {output_path} …")
subprocess.run([
    "docker", "cp",
    f"{CONTAINER}:/tmp/insurance_ai_dump.sql",
    output_path
], check=True)

print("Stopping Docker containers …")
subprocess.run(["docker-compose", "down"], check=True)

print("All done. Fresh dump saved to ./init/insurance_ai_dump.sql and containers stopped.")
