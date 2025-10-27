#new dropperrrr, keeping old one just in case/proof of work lol

import curses, time, random
from levels import LEVELS

PLAYER_CHAR = "@"
OB_CHAR = "#"
EMPTY = " "
BORDER = "|"
TOP_BOTTOM = "-"

TICK = 1/60

LEFT_KEYS = {curses.KEY_LEFT, ord('a'), ord('h')}
RIGHT_KEYS = {curses.KEY_RIGHT, ord('d'), ord('l')}
PAUSE_KEYS = {ord('p')}
QUIT_KEYS = {27, ord('q')}

RESTART_KEYS = {ord('r')}

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


def level_intro(stdscr, name, idx, total):
    stdscr.clear()
    title = f"Level {idx+1}/{total}: {name}"
    draw_text(stdscr, 2, 2, title)
    draw_text(stdscr, 4, 2, "Press any key to start, or Q to quit…")
    ch = stdscr.getch()
    if ch in QUIT_KEYS:
        stdscr.nodelay(False)
        return False
    return True


def play_level(stdscr, bounds, cfg):
    stdscr.nodelay(True)
    name = cfg["name"]
    survive_seconds = cfg["survive_seconds"]
    start_gap_width = cfg["start_gap_width"]
    min_gap_width = cfg["min_gap_width"]
    fall_start_sec = cfg["fall_start_sec"]
    fall_min_sec = cfg["fall_min_sec"]
    fall_mult_per_point = cfg["fall_mult_per_point"]
    speedup_every = cfg["speedup_every"]
    speedup_factor = cfg["speedup_factor"]
    player_step = cfg["player_step"]

    rows_apart = cfg.get("rows_apart_start", 3.5)
    rows_apart_min = cfg.get("rows_apart_min", 2.0)
    rows_apart_decay_per_sec = cfg.get("rows_apart_decay_per_sec", 0.02)
    fall_rate_per_sec = cfg.get("fall_rate_per_sec", 0.05)

    left, right, top, bottom = bounds

    player_y = bottom-2
    player_x = (left + right) // 2
    rows = []
    gap_width = start_gap_width
    survived_rows = 0
    alive = True
    paused = False

    fall_dt = fall_start_sec
    last_fall = time.time()

    spawn_dt = max(0.08, fall_dt * rows_apart)
    last_spawn = time.time() - spawn_dt * 0.4

    elapsed_alive = 0.0
    prev = time.time()

    while True:
        now = time.time()
        dt = now - prev
        prev = now

        ch = stdscr.getch()
        if ch != -1:
            if ch in QUIT_KEYS:
                stdscr.nodelay(False)
                return "quit"
            if ch == curses.KEY_RESIZE:
                pass
            elif ch in PAUSE_KEYS and alive:
                paused = not paused
            elif ch in RESTART_KEYS and not alive:
                stdscr.nodelay(False)
                return "retry"
            elif alive and not paused:
                if ch in LEFT_KEYS:
                    player_x -= player_step
                elif ch in RIGHT_KEYS:
                    player_x += player_step
                player_x = clamp(player_x, left+1, right-1)

        if alive and not paused:
            elapsed_alive += dt
            if elapsed_alive >= survive_seconds:
                stdscr.nodelay(False)
                return "win"

            fall_dt = max(fall_min_sec, fall_dt * (1.0 - fall_rate_per_sec * dt))
            rows_apart = max(rows_apart_min, rows_apart - rows_apart_decay_per_sec * dt)
            spawn_dt = max(0.08, fall_dt * rows_apart)

            if time.time() - last_spawn >= spawn_dt:
                play_w = (right - left - 1)
                gw = gap_width
                if gw > play_w - 2:
                    gw = max(3, play_w // 3)
                gap_start = random.randint(left+1, right - gw - 1)
                rows.append(Row(y=top+1, gap_start=gap_start, gap_width=gw))
                last_spawn = time.time()

            if time.time() - last_fall >= fall_dt:
                for r in rows:
                    r.y += 1
                last_fall = time.time()

            next_rows = []
            for r in rows:
                if r.y == player_y:
                    if not (r.gap_start <= player_x < r.gap_start + r.gap_width):
                        alive = False
                    else:
                        survived_rows += 1
                        fall_dt = max(fall_min_sec, fall_dt * fall_mult_per_point)
                        if survived_rows % speedup_every == 0:
                            gap_width = max(min_gap_width, gap_width - 1)
                if r.y <= bottom - 1:
                    next_rows.append(r)
            rows = next_rows                 

        stdscr.erase()
        draw_hline(stdscr, top, left, right, TOP_BOTTOM)
        draw_hline(stdscr, bottom, left, right, TOP_BOTTOM)
        for y in range(top+1, bottom):
            try:
                stdscr.addch(y, left, BORDER)
                stdscr.addch(y, right, BORDER)
            except curses.error:
                pass

        remaining = max(0, int(survive_seconds - elapsed_alive))
        hud = (
            f" {name} | Time:{remaining:>2}s  Rows:{survived_rows}"
            f"  Gap:{gap_width}  Spawn:{spawn_dt:.2f}s  Fall:{fall_dt:.2f}s"
            "  [←/→ A/D] (P)ause (R)etry (Q)uit "
        )
        draw_text(stdscr, 0, 0, hud[:curses.COLS-1])

        for r in rows:
            y = r.y
            if top < y < bottom:
                draw_hline(stdscr, y, left+1, right-1, OB_CHAR)
                for x in range(r.gap_start, r.gap_start + r.gap_width):
                    if left < x < right:
                        try: stdscr.addch(y, x, EMPTY)
                        except curses.error: pass

        try:
            stdscr.addch(player_y, player_x, PLAYER_CHAR)
        except curses.error:
            pass

        if paused:
            msg = "[PAUSED] press P to resume"
            draw_text(stdscr, (top+bottom)//2, (curses.COLS - len(msg))//2, msg)
        if not alive:
            msg1 = "You crashed!"
            msg2 = f"Rows passed: {survived_rows}  |  Press R to retry level or Q to quit"
            draw_text(stdscr, (top+bottom)//2, (curses.COLS - len(msg1))//2, msg1)
            draw_text(stdscr, (top+bottom)//2 + 1, (curses.COLS - len(msg2))//2, msg2)

        stdscr.refresh()
        if dt < TICK:
            time.sleep(TICK - dt)

def run(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.keypad(True)
    curses.use_default_colors()

    def compute_bounds():
        h, w = stdscr.getmaxyx()
        left, right = 2, w-3
        top, bottom = 2, h-3
        return (left, right, top, bottom)
    
    minw, minh = 30, 16
    while True:
        h, w = stdscr.getmaxyx()
        if w >= minw and h >= minh: break
        stdscr.clear()
        draw_text(stdscr, 0, 0, f"Resize terminal to at least {minw}x{minh}. Press any key…")
        stdscr.getch()
    
    total = len(LEVELS)
    for i, cfg in enumerate(LEVELS):
        if not level_intro(stdscr, cfg["name"], i, total):
            return
        outcome = play_level(stdscr, compute_bounds(), cfg)
        if outcome == "quit":
            return
        elif outcome == "retry":
            if not level_intro(stdscr, cfg["name"], i, total):
                return
            outcome = play_level(stdscr, compute_bounds(), cfg)
            if outcome in ("quit", "retry"):
                if outcome == "quit":
                    return
                continue
        elif outcome == "win":
            stdscr.clear()
            msg = f"✔ Level {i+1} complete!"
            draw_text(stdscr, 0, 0, msg)
            stdscr.refresh()
            time.sleep(0.9)
    
    stdscr.clear()
    draw_text(stdscr, 0, 0, "🏆 You cleared all levels! Press any key to exit.")
    stdscr.getch()

def main():
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()

# hi reviewers :)