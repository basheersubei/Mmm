#Mmm: A simple terminal-based text editor

import sys, tty, termios

class Editor:
    def __init__(self):
        self._lines = []
        self._cursor = Cursor(1, 1)
        with open("test.txt") as lines:
            for line in lines:
                self._lines.append(line.rstrip('\n'))      
        self._buffer = Buffer(self._lines)

    def run(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        try:
            tty.setraw(sys.stdin.fileno())
            while 1:
                self.render()
                self.handle_input()
        finally:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def handle_input(self):
        getch = _GetchUnix()
        char = getch()
        if char == chr(17): # Ctrl+Q
            sys.stdout.write("\033[37;41mQUIT\033[39;49m\r\n")
            sys.exit(0)
        elif char == chr(9): # Ctrl+H
            sys.stdout.write("H")
        elif char == chr(10): # Ctrl+J
            sys.stdout.write("J")
        elif char == chr(11): # Ctrl+K
            sys.stdout.write("K")
        elif char == chr(12): # Ctrl+L
            sys.stdout.write("L")
                    
    def render(self):
        ANSI.clear_screen()
        ANSI.move_cursor(0, 0)
        self._buffer.render()
        ANSI.move_cursor(self._cursor._row, self._cursor._col)
        sys.stdout.flush() # Cursor move is buffered if i dont do this :/
        
class Buffer:
    def __init__(self, lines):
        self._lines = lines
    
    def render(self):
        for line in self._lines:
            sys.stdout.write(line + "\r\n")
            #sys.stdout.flush() # Not required in raw mode apparently
            
class Cursor:
    def __init__(self, row = 0, col = 0):
        self._row = row
        self._col = col

class ANSI:
    def clear_screen():
        sys.stdout.write("\033[2J")

    def move_cursor(row, col):
        sys.stdout.write("\033[{};{}H".format(row + 1, col + 1))

# Gets a single char input. Code copied from StackOverflow
class _GetchUnix:
    def __call__(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

e = Editor()
e.run()
