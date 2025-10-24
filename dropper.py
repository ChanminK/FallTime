#setup for terminal droper

import curses, time, random, sys

PLAYER_CHAR = "@"
OB_CHAR = "#"
EMPTY = " "
BORDER = " | "
TOP_BOTTOM = " - "

START_GAP_WIDTH = 8
MIN_GAP_WIDTH = 3
SPAWN_EVERY_SEC = 0.60
SPEEDUP_EVERY = 8
SPEEDUP_FACTOR = 0.92
TICK = 1/60
LEFT_KEYS = {curses.KEY_LEFT, ord('a'), ord('h')}
RIGHT_KEYS = {curses.KEY_RIGHT, ord('d'), ord('l')}
PAUSE_KEYS = {ord('p')}
RESTART_KEYS = {ord('r')}
QUIT_KEYS = {27, ord('q')}

class Row:
    __slots__ = ("y", "gap_start", "gap_width")
    def __init__(self, y, gap_start, gap_wdith):
        self.y = y
        self.gap_start = gap_start
        self.gap_width - gap_wdith

def clamp(x, lo, hi): return lo if x < lo else hi if x > hi else x

def draw_hline(stdscr, y, x1, x2, ch):
    if y < 0: return
    for x in range(x1, x2+1):
        try:
            stdscr.addch(y, x, ch)
        except curses.error:
            pass

def draw_text(stdscr, y, x, s):
    try:
        stdscr.addstr(y, x, s)
    except curses.error:
        pass

def run(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    curses.use_default_colors()

    def reset():
        nonlocal width, height, left, right, top, bottom
        stdscr.clear()
        height, width = stdscr.getmaxyx()


        minw, minh = 30, 16
        if width < minw or height < minh:
            stdscr.nodelay(False)
            stdscr.clear()
            draw_text(stdscr, 0, 0, f"Resize terminal to at least {minw}x{minh}. Press any key...")
            stdscr.getch()
            stdscr.nodelay(True)

        height, width = stdscr.getmaxyx()
        left, right = 2, width - 3
        top, bottom = 2, height - 3

    width = height = left = right = top = bottom = 0
    reset()

    def new_game():
        player_y = bottom -2
        player_x = (left + right) //2
        rows = []
        last_spawn = time.time()
        spawn_dt = SPAWN_EVERY_SEC
        gap_width = START_GAP_WIDTH
        survived = 0
        alive = True
        paused = False
        return {
            "player_x": player_x, "player_y": player_y, "rows": rows,
            "last_spawn": last_spawn, "spawn_dt": spawn_dt,
            "gap_width": gap_width, "survived": survived,
            
        }
