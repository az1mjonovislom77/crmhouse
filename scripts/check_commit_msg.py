import re
import sys

ALLOWED_PATTERN = re.compile(
    r"^(feat|fix|refactor|perf|docs|test|chore|ci|build|style|revert)(\([\w\-. ]+\))?!?: .{10,}",
)
BYPASS_PREFIXES = ("Merge", "Revert", "fixup!", "squash!")


def main() -> int:
    with open(sys.argv[1], encoding="utf-8") as f:
        message = f.readline().strip()

    if not message or message.startswith(BYPASS_PREFIXES):
        return 0

    if ALLOWED_PATTERN.match(message):
        return 0

    print("Commit xabari qoidaga mos emas.")
    print(f"  Yozilgan:  {message!r}")
    print("  Format:    type: tavsif  (tavsif kamida 10 belgi)")
    print("  Turlar:    feat, fix, refactor, perf, docs, test, chore, ci, build, style, revert")
    print("  Masalan:   fix: CDR ro'yxatiga organization scoping qo'shildi")
    return 1


if __name__ == "__main__":
    sys.exit(main())
