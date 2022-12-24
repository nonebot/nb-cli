from pyfiglet import figlet_format


def draw_logo() -> str:
    return figlet_format("NoneBot", font="basic").strip()
