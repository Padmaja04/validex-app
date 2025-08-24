# merge_requirements.py

files = ["requirements1.txt", "requirements2.txt"]
unique_packages = set()

for file in files:
    with open(file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                unique_packages.add(line)

with open("requirements.txt", "w") as out:
    for pkg in sorted(unique_packages):
        out.write(pkg + "\n")

print("✅ Merged and cleaned requirements.txt")
