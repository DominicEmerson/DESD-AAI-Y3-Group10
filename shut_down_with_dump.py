import subprocess  # Import subprocess for running shell commands
import os  # Import os for file path handling

CONTAINER = "desd-aai-y3-group10-database-1"  # Name of the PostgreSQL container

print("Dumping PostgreSQL database inside container …")  # Inform user about the dump process
subprocess.run([
    "docker", "exec", CONTAINER,  # Execute command inside the container
    "pg_dump", "-U", "user", "-d", "insurance_ai",  # Command to dump the database
    "--encoding=UTF8", "--format=plain", "-f", "/tmp/insurance_ai_dump.sql"  # Dump options
], check=True)  # Raise an error if the command fails

output_path = os.path.join("init", "insurance_ai_dump.sql")  # Path to save the dump file
print(f"Copying dump file to {output_path} …")  # Inform user about the copy process
subprocess.run([
    "docker", "cp",  # Copy command
    f"{CONTAINER}:/tmp/insurance_ai_dump.sql",  # Source path in the container
    output_path  # Destination path on the host
], check=True)  # Raise an error if the command fails

print("Stopping Docker containers …")  # Inform user about stopping containers
subprocess.run(["docker-compose", "down"], check=True)  # Stop all Docker containers

print("All done. Fresh dump saved to ./init/insurance_ai_dump.sql and containers stopped.")  # Inform user that the process is complete
