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


class Brainfuck:
  """Run brainfuck code."""
  ptr: int
  pc: int
  cells: bytearray
  code: str
  charset: BrainfuckCharset

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
    print(chr(self.cells[self.ptr]), end='', flush=True)

  def input(self) -> None:
    self.cells[self.ptr] = (ord(getch()) % 256) # % 256 for safety idk if getch can return >255



  def __init__(
    self,
    code: str,
    *,
    cell_number: int = 30000,
    charset: BrainfuckCharset = BrainfuckCharset(),
    _debug: bool = False,
  ) -> None:
    self.code = code
    self.charset = charset

    self.ptr = 0
    self.pc = 0
    self.cells = bytearray(cell_number)

    self.strip_code()
    self.raise_for_syntax()
    self.filter_code()


    while True:
      if self.pc >= len(self.code):
        break

      char = self.code[self.pc]

      if _debug:
        import tcrutils as tcr
        tcr.c(char, self.pc)

      if char == self.charset.inc_ptr:
        self.inc_ptr()
      elif char == self.charset.dec_ptr:
        self.dec_ptr()
      elif char == self.charset.inc_val:
        self.inc_val()
      elif char == self.charset.dec_val:
        self.dec_val()
      elif char == self.charset.output:
        self.output()
      elif char == self.charset.input:
        self.input()
      elif char == self.charset.loop_start:
        pass # do nothing, proceed to the next character
      elif char == self.charset.loop_end:
        if self.cells[self.ptr]:
          while self.code[self.pc] != self.charset.loop_start:
            self.pc -= 1
      else:
        raise RuntimeError(f'Invalid character in code: {char!r} (somehow not filtered?)')

      self.pc += 1
