
def print_color(msg, mode="INFO", end="\n"):
    colors = {
        "INFO": "\033[97m",  # white
        "ERROR": "\033[31m",  # red
        "WARNING": "\033[33m",  # yellow
    }
    try:
        color = colors[mode]
    except KeyError:
        color = colors["INFO"]
    print(color + str(msg) + "\033[0m", end=end)

