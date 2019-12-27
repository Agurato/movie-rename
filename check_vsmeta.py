import os
import sys

if __name__ == "__main__":
    path = sys.argv[1]

    for root, dir, files in os.walk(path):
        for f in files:
            if not f.endswith(".vsmeta") and f + ".vsmeta" not in files:
                print(f)
