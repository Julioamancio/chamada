import sys
from pathlib import Path

p = Path(sys.argv[1])
data = p.read_bytes()
def chk(label, b):
    print(f"{label}:", (b in data))

print("len:", len(data))
chk("bulk_attendance_range", b"bulk_attendance_range")
chk("bulk_attendance_auto_range", b"bulk_attendance_auto_range")
chk("bulk_attendance_auto_stage", b"bulk_attendance_auto_stage")
chk("rate_field", b"name=\"rate\"")
