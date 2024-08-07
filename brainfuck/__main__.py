import curses
import pathlib as p
from functools import wraps

import arguably
import tcrutils as tcr
from src.bf import Brainfuck, BrainfuckHooks, BrainfuckSyntaxError
from src.getch import getch


def target_only(func):
  @wraps(func)
  def wrapper(*args, **kwargs):
    if arguably.is_target():
      func(*args, **kwargs)

  return wrapper


# bf = Brainfuck(
#   ',+.',
#   cell_number=10,
#   _debug=False,
# )


@arguably.command
@target_only
def __root__(
  file: str,
  *,
  cells: int = 30000,
  interactive: float | None = None,
  text: bool = False,
  wait: bool = False,
  sleepless_interactive: bool = False,
  skip_brackets_interactive: bool = False,
  max_resolution: tuple[int, int] | None = None,
) -> None:
  """Run brainfuck code from a file.

  Args:
    file: The file to contain brainfuck code.
    cells: [-n] The number of cells.
    debug: [-d] Run in debug mode [requires tcrutils pypi package].
    interactive: [-i] If set, run in interactive mode and wait this many seconds between frames.
    sleepless_interactive: [-l] If set, run in interactive mode without waiting between frames.
    text: [-t] If set, interpret the first positional argument as brainfuck code, not a path to a file.
    wait: [-w] Wait for a keypress before exiting.
    skip_brackets_interactive: [-b] Skip the interactive frame where the cursor is about to backtrack to the loop's beginning
    max_resolution: [-r] Set the maximum resolution of the interactive cells display.
  """

  if text:
    bf_code = file
  else:
    file = p.Path(file)
    if not file.is_file():
      arguably.error('File not found.')
    bf_code = file.read_text(encoding='utf-8')

  interactive, interactive_delay = interactive is not None, max(0, interactive)

  if sleepless_interactive:
    interactive_delay = 0
    interactive = True

  if interactive:
    import time

    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    curses.curs_set(1)

    start_time = time.time()
    first_frame = True

    def get_interactive_hooks() -> BrainfuckHooks:
      printqueue: list[str] = []

      def before_frame(bf: Brainfuck) -> bool:
        return False  # False = continue execution

      def after_frame(bf: Brainfuck) -> bool:
        nonlocal first_frame
        first_frame = False

        if bf.previous_code_char == ']' and skip_brackets_interactive and bf.previous_cell_value:
          bf.frames -= 1
          return False # continue

        stdscr.clear()

        maxbatch = max(0, min(tcr.terminal.width // 3 - 10, max_resolution[0] if max_resolution is not None else 99999999999))
        maxcells = max(0, min((curses.LINES - 6)*maxbatch, (max_resolution[1] if max_resolution is not None else 99999999999)*maxbatch))
        if maxcells:
          batches = tcr.batched(bf.cells[:maxcells], maxbatch)

          batches: list[list[str]] = [[tcr.fmt_iterable(tcr.types.HexInt(cell, leading_zeroes=2, prefix='')) for cell in batch] for batch in batches]

          # batches = '\n'.join(' '.join(batch) for batch in batches)

          for j, batch in enumerate(batches):
            if j: stdscr.addstr('\n')

            for i, cell in enumerate(batch):
              pos = j*maxbatch + i

              attr = 0
              if pos == bf.ptr:
                attr = curses.A_BOLD

              stdscr.addstr(cell + ' ', attr)

          if maxcells < len(bf.cells):
            attr = 0
            if bf.ptr >= maxcells:
              attr = curses.A_BOLD

            stdscr.addstr(f'(+{len(bf.cells) - maxcells}) ', attr)

          stdscr.addstr('\n')

        fifth_row = curses.LINES - 6
        stdscr.addstr(fifth_row, 0, '')

        fourth_row = curses.LINES - 5
        uptime = time.time() - start_time
        fps = (bf.frames / uptime) if uptime else 0
        stdscr.addstr(fourth_row, 0, f'frames={bf.frames} uptime={uptime:.0f} avg_fps={fps:.2f} pc={bf.pc} ptr={bf.ptr} instr={bf.previous_code_char} cell={tcr.hex(bf.current_cell_value, leading_zeroes=2, prefix="")}')

        third_row = curses.LINES - 4
        stdscr.addstr(third_row, 0, repr(''.join(printqueue).replace("'", chr(9999)))[1:-1].replace(chr(9999), "'"))

        second_row = curses.LINES - 3
        stdscr.addstr(second_row, 0, bf.code)

        first_row = curses.LINES - 2
        stdscr.addstr(first_row, 0, (bf.pc-1) * ' ' + '^')

        stdscr.refresh()

        time.sleep(interactive_delay)

        return False  # False = continue execution

      def printhook(s: str) -> None:
        printqueue.append(s)

      return BrainfuckHooks(before_frame=before_frame, after_frame=after_frame, print=printhook)

  try:
    Brainfuck(bf_code, cell_number=cells, **({} if not interactive else {'hooks': get_interactive_hooks()}))
  except BrainfuckSyntaxError as e:
    print(e)
    exit(1)
  except KeyboardInterrupt:
    exit(0)
  else:
    if wait:
      if interactive:
        stdscr.addstr(curses.LINES - 1, 0, 'Press any key to continue...')
        try:
          stdscr.getch()
        except KeyboardInterrupt:
          pass
      else:
        print('\nPress any key to continue...', end='\r', flush=True)
        getch()
        print( '                             ', end='\r', flush=True)
  finally:
    if interactive:
      curses.curs_set(1)
      curses.nocbreak()
      stdscr.keypad(False)
      curses.echo()
      curses.endwin()


if __name__ == '__main__':
  arguably.run(name='brainfuck')
