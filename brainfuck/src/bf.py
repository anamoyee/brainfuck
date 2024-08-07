from collections.abc import Callable
from dataclasses import dataclass

from .getch import getch


class BrainfuckSyntaxError(SyntaxError):
  """Represents a syntax error in brainfuck code."""


@dataclass
class BrainfuckCharset:
  inc_ptr: str = '>'
  dec_ptr: str = '<'
  inc_val: str = '+'
  dec_val: str = '-'
  output: str = '.'
  input: str = ','
  loop_start: str = '['
  loop_end: str = ']'

  def full_charset(self) -> str:
    return f'{self.inc_ptr}{self.dec_ptr}{self.inc_val}{self.dec_val}{self.output}{self.input}{self.loop_start}{self.loop_end}'


@dataclass
class BrainfuckHooks:
  """Hooks for hooking into various brainfuck events."""

  before_frame: Callable[['Brainfuck'], bool] = lambda _: False
  """Ran before a frame is started. When True is returned, the interpreter will exit as if it reached the end of the code."""
  after_frame: Callable[['Brainfuck'], bool] = lambda _: False
  """Ran after a frame is finished. When True is returned, the interpreter will exit as if it reached the end of the code."""
  print: Callable[[str], None] = lambda s: print(s, end='', flush=True)
  """Flushing, no end printing function."""


class Brainfuck:
  """Run brainfuck code."""

  ptr: int
  pc: int
  frames: int

  cells: bytearray
  code: str

  charset: BrainfuckCharset
  hooks: BrainfuckHooks

  def strip_code(self) -> None:
    self.code = self.code.rstrip()

  def raise_for_syntax(self) -> None:
    brackets = 0

    for i, char in enumerate(self.code):
      if char == self.charset.loop_start:
        brackets += 1
      elif char == self.charset.loop_end:
        brackets -= 1
        if brackets < 0:
          raise BrainfuckSyntaxError(f'{self.__class__.__name__}: unmatched {self.charset.loop_end!r} at position {i}\n{self.code}\n{" " * i}^')

    if brackets != 0:
      i = len(self.code) - 1
      raise BrainfuckSyntaxError(f'{self.__class__.__name__}: unmatched {self.charset.loop_start!r} at position {i}\n{self.code}\n{" " * i}^')

  def filter_code(self) -> str:
    self.code = ''.join(filter(lambda x: x in self.charset.full_charset(), self.code))

  def inc_ptr(self) -> None:
    self.ptr += 1
    self.ptr %= len(self.cells)

  def dec_ptr(self) -> None:
    self.ptr -= 1
    self.ptr %= len(self.cells)

  def inc_val(self) -> None:
    self.cells[self.ptr] = (self.cells[self.ptr] + 1) % 256

  def dec_val(self) -> None:
    self.cells[self.ptr] = (self.cells[self.ptr] - 1) % 256

  def output(self) -> None:
    self.hooks.print(chr(self.cells[self.ptr]))

  def input(self) -> None:
    self.cells[self.ptr] = ord(getch()) % 256  # % 256 for safety idk if getch can return >255

  previous_code_char: str
  previous_cell_value: str

  @property
  def current_code_char(self) -> str:
    return self.code[self.pc]

  @property
  def current_cell_value(self) -> int:
    return self.cells[self.ptr]

  def __init__(
    self,
    code: str,
    *,
    cell_number: int = 30000,
    charset: BrainfuckCharset = BrainfuckCharset(),
    hooks: BrainfuckHooks = BrainfuckHooks(),
    _debug: bool = False,
  ) -> None:
    self.code = code
    self.charset = charset
    self.hooks = hooks

    self.ptr = 0
    self.pc = 0
    self.frames = 0

    try:
      self.cells = bytearray(cell_number)
    except (MemoryError, OverflowError):
      print(f'\nYour cell_number of {cell_number} is {"bogus" if cell_number >= 10**8 else "too big"}. You don\'t have enough memory to host this many cells.')
      exit(1)

    self.strip_code()
    self.raise_for_syntax()
    self.filter_code()

    while True:
      if self.pc >= len(self.code):
        break

      if self.hooks.before_frame(self):
        break

      self.previous_cell_value = self.current_cell_value
      self.previous_code_char = self.current_code_char

      if _debug:
        import tcrutils as tcr

        tcr.c(self.current_code_char, self.pc)

      if self.current_code_char == self.charset.inc_ptr:
        self.inc_ptr()
      elif self.current_code_char == self.charset.dec_ptr:
        self.dec_ptr()
      elif self.current_code_char == self.charset.inc_val:
        self.inc_val()
      elif self.current_code_char == self.charset.dec_val:
        self.dec_val()
      elif self.current_code_char == self.charset.output:
        self.output()
      elif self.current_code_char == self.charset.input:
        self.input()
      elif self.current_code_char == self.charset.loop_start:
        pass  # do nothing, proceed to the next character
      elif self.current_code_char == self.charset.loop_end:
        if self.current_cell_value:
          brackets = 1
          while brackets:
            self.pc -= 1
            if self.current_code_char == self.charset.loop_start:
              brackets -= 1
            elif self.current_code_char == self.charset.loop_end:
              brackets += 1
      else:
        raise RuntimeError(f'Invalid character in code: {self.current_code_char!r} (somehow not filtered?)')

      self.pc += 1
      self.frames += 1

      if self.hooks.after_frame(self):
        break
