import os

if os.name == 'nt':
  import msvcrt
else:
  import sys
  import termios
  import tty


def getch():
  if os.name == 'nt':
    return msvcrt.getch().decode()

  fd = sys.stdin.fileno()
  old_settings = termios.tcgetattr(fd)
  try:
    tty.setraw(sys.stdin.fileno())
    ch = sys.stdin.read(1)
  finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
  return ch

if __name__ == '__main__':
  print('>>> ', end='', flush=True)
  print(getch())
