import pathlib as p
from functools import wraps

import arguably
from src.bf import Brainfuck, BrainfuckSyntaxError


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
def __root__(file: p.Path, *, cells: int = 30000, debug: bool = False) -> None:
  """Run brainfuck code from a file.

  Args:
    file: The file to contain brainfuck code.
    cells: [-n] The number of cells.
    debug: [-d] Run in debug mode [requires tcrutils pypi package].
  """
  if not file.is_file():
    arguably.error('File not found.')

  bf_code = file.read_text(encoding='utf-8')

  try:
    Brainfuck(
      bf_code,
      cell_number=cells,
      _debug=debug,
    )
  except BrainfuckSyntaxError as e:
    print(e)
    exit(1)


if __name__ == '__main__':
  arguably.run(name='brainfuck')
