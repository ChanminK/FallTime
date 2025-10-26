#setup for terminal droper

import curses, time, random, sys

PLAYER_CHAR = "@"
OB_CHAR = "#"
EMPTY = " "
BORDER = "|"
TOP_BOTTOM = "-"

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

ROW_STEP_SEC = 0.10
MIN_ROW_STEP_SEC = 0.03
PLAYER_STEP = 2

class Row:
    __slots__ = ("y", "gap_start", "gap_width")
    def __init__(self, y, gap_start, gap_width):
        self.y = y
        self.gap_start = gap_start
        self.gap_width = gap_width

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
        fall_dt = ROW_STEP_SEC
        last_fall = time.time()
        return {
            "player_x": player_x, "player_y": player_y, "rows": rows,
            "last_spawn": last_spawn, "spawn_dt": spawn_dt,
            "gap_width": gap_width, "survived": survived,
            "alive": alive, "paused": paused,
            "fall_dt": fall_dt, "last_fall": last_fall
        }
    
    g = new_game()

    while True:
        t0 = time.time()

        ch = stdscr.getch()
        if ch != -1:
            if ch in QUIT_KEYS:
                return
            if ch == curses.KEY_RESIZE:
                reset()
                
                #PLAYER BOUNDS TO SCREW AROUND WITH
                g["player_x"] = clamp(g["player_x"], left+1, right-1)
            elif ch in PAUSE_KEYS and g["alive"]:
                g["paused"] = not g["paused"]
            elif ch in RESTART_KEYS and not g["alive"]:
                g = new_game()
            elif g["alive"] and not g["paused"]:
                if ch in LEFT_KEYS:
                    g["player_x"] -= 1
                elif ch in RIGHT_KEYS:
                    g["player_x"] += 1
                g["player_x"] = clamp(g["player_x"], left+1, right-1)

        if g["alive"] and not g["paused"]:
            if time.time() - g["last_spawn"] >= g["spawn_dt"]:
                play_w = (right - left - 1)
                gap_w = g["gap_width"]
                if gap_w > play_w -2:
                    gap_w = max(3, play_w // 3)
                gap_start = random.randint(left+1, right - gap_w -1)
                g["rows"].append(Row(y=top+1, gap_start=gap_start, gap_width=gap_w))
                g["last_spawn"] = time.time()

            now = time.time()
            if now - g["last_spawn"] >= g["fall_dt"]:
                for r in g["rows"]:
                    r.y += 1
                g["last_fall"]

            next_rows = []
            for r in g["rows"]:
                if r.y == g["player_y"]:
                    if not (r.gap_start <= g["player_x"] < r.gap_start + r.gap_width):
                        g["alive"] = False
                    else:
                        g["survived"] += 1
                        if g["survived"] % SPEEDUP_EVERY == 0:
                            g["spawn_dt"] = max(0.15, g["spawn_dt"] & SPEEDUP_FACTOR)
                            g["gap_width"] = max(MIN_GAP_WIDTH, g["gap_width"] -1)
                            g["fall_dt"] = max(MIN_ROW_STEP_SEC, g["fall_dt"] * SPEEDUP_FACTOR )
                if r.y <= bottom -1:
                    next_rows.append(r)
            g["rows"] = next_rows
        
        stdscr.erase()

        draw_hline(stdscr, top, left, right, TOP_BOTTOM)
        draw_hline(stdscr, bottom, left, right, TOP_BOTTOM)
        for y in range(top+1, bottom):
            try:
                stdscr.addch(y, left, BORDER)
                stdscr.addch(y, right, BORDER)
            except curses.error:
                pass
        
        hud = f" Terminal Dropper | Score: {g['survived']} Gap:{g['gap_width']} Spawn:{g['spawn_dt']:.2f}s [←/→ or A/D]  (P)ause  (R)estart  (Q)uit "
        draw_text(stdscr, 0, 0, hud[:max(0, width-1)])

        for r in g["rows"]:
            y = r.y
            if top < y < bottom:
                draw_hline(stdscr, y, left+1, right-1, OB_CHAR)
                for x in range(r.gap_start, r.gap_start + r.gap_width):
                    if left < x < right:
                        try: stdscr.addch(y, x, EMPTY)
                        except curses.error: pass
                
        try:
            stdscr.addch(g["player_y"], g["player_x"], PLAYER_CHAR)
        except curses.error:
            pass

        if g["paused"]:
            msg = "[PAUSED] press P to resume"
            draw_text(stdscr, (top+bottom)//2, (width - len(msg))//2, msg)

        if not g["alive"]:
            msg1 = "You crashed!"
            msg2 = f"Score: {g['survived']} Press R to restart or Q to quit!"
            draw_text(stdscr, (top+bottom)//2, (width - len(msg1))//2, msg1)
            draw_text(stdscr, (top+bottom)//2 + 1, (width - len(msg2))//2, msg2)

        stdscr.refresh()

        dt = time.time() -t0
        if dt < TICK:
            time.sleep(TICK - dt)

def main():
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
    
