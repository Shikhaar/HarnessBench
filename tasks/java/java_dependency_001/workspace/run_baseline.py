import sys
from pathlib import Path

xml_text = Path("pom.xml").read_text(encoding="utf-8")
assert "<groupId>com.example</groupId>" in xml_text
assert "legacy-connector" in xml_text
print("Baseline passed")
sys.exit(0)
