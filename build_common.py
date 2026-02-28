import sys

def read_settings():
    settings = dict()
    with open("settings.txt", "r") as f:
        for line in f:
            line = line.strip()
            if len(line) == 0 or line.startswith(";"):
                continue
            if not " " in line:
                build_error("Invalid line in settings.txt: '{}'".format(line))
            space_pos = line.find(" ")
            key = line[:space_pos]
            value = line[space_pos + 1:]
            settings[key] = value
            print("{} = {}".format(key, value))
    return settings

settings = read_settings()

def build_error(msg):
    print("BUILD ERROR!:")
    print(msg)
    sys.exit(1)
