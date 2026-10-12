HELP_MENU = [
    [("YOTSUBA-CLI HELP", "subject")],
    [("", "default")],

    [("NAVIGATION", "subject")],
    [("j / Down Arrow".ljust(18), "post_number"),
     ("Scroll down", "default")],

    [("k / Up Arrow".ljust(18), "post_number"),
     ("Scroll up", "default")],

    [("J / Page Down".ljust(18), "post_number"),
     ("Page down", "default")],

    [("K / Page Up".ljust(18), "post_number"),
     ("Page up", "default")],

    [("g / Home".ljust(18), "post_number"),
     ("Jump to top", "default")],

    [("G / End".ljust(18), "post_number"),
     ("Jump to bottom", "default")],

    [("/".ljust(18), "post_number"),
     ("Enter command mode", "default")],

    [("Tab".ljust(18), "post_number"),
     ("Open quick menu", "default")],

    [("?".ljust(18), "post_number"),
     ("Open this help page", "default")],

    [("q".ljust(18), "post_number"),
     ("Quit", "default")],

    [("", "default")],

    [("COMMANDS", "subject")],

    [("/listboards", "board_highlight")],
    [("    Show the available boards.", "default")],

    [("", "default")],

    [("/board [board] [page]", "board_highlight")],
    [("    Open a board index.", "default")],
    [("    If no page is given, page 1 is used.", "default")],
    [("    Example: /board g", "default")],
    [("    Example: /board v 3", "default")],

    [("", "default")],

    [("/thread [board] [number]", "board_highlight")],
    [("    Open a thread from the currently loaded board index.",
      "default")],
    [("    [number] is the local thread number shown in the index,",
      "default")],
    [("    not the actual 4chan thread ID.", "default")],
    [("    Example: /thread g 5", "default")],

    [("", "default")],

    [("/image [board] [number]", "board_highlight")],
    [("    Open the media belonging to a thread using mpv.",
      "default")],
    [("    [number] uses the same local index numbering as /thread.",
      "default")],
    [("    Example: /image g 5", "default")],

    [("", "default")],

    [("QUICK MENU", "subject")],
    [("Press Tab to open the quick menu.", "default")],

    [("", "default")],

    [("boards", "name"),
     ("    Open the board list.", "default")],

    [("thread", "name"),
     ("    Choose a thread from the current board index.", "default")],

    [("images", "name"),
     ("    Choose a thread and open its media in mpv.", "default")],

    [("help", "name"),
     ("      Open this help page.", "default")],

    [("", "default")],

    [("Arrow Keys", "post_number"),
     ("    Move through menu entries.", "default")],

    [("Enter", "post_number"),
     (" "*9, "default"),
     ("Select an entry.", "default")],

    [("Esc", "post_number"),
     (" "*11, "default"),
     ("Return to the previous menu or close the menu.", "default")],

    [("", "default")],

    [("THREAD NUMBERS", "subject")],
    [("Thread numbers shown by yotsuba-cli are contextual shortcuts.",
      "default")],

    [("", "default")],

    [("[1] Thread A", "post_number")],
    [("[2] Thread B", "post_number")],
    [("[3] Thread C", "post_number")],

    [("", "default")],

    [("/thread g 2", "board_highlight")],
    [("    Opens Thread B.", "default")],

    [("", "default")],

    [("These numbers only belong to the board index that produced them.",
      "default")],
    [("A /g/ index number cannot be used as a /v/ index number.",
      "default")],

    [("", "default")],

    [("MEDIA", "subject")],
    [("yotsuba-cli delegates thread media to mpv.", "default")],
    [("This includes images, GIFs, video, and other supported media.",
      "default")],

    [("", "default")],

    [("RESIZING", "subject")],
    [("The interface automatically adjusts when the terminal is resized.",
      "default")],

    [("", "default")],

    [("ABOUT", "subject")],
    [("yotsuba-cli", "name")],
    [("A curses-based 4chan client written in Python.", "default")],
]

def get():
    return HELP_MENU
