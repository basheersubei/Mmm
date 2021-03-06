#Mmm: A simple terminal-based text editor

import sys, tty, termios, copy, shutil

class Editor:
    def __init__(self):
        self._lines = []
        self._cursor = Cursor(0, 0)
        self._history = []
        self._min_row = 0
        self._terminal_dimensions = shutil.get_terminal_size()
        self._max_row = self._terminal_dimensions.lines - 1
        with open("test.txt") as lines:
            for line in lines:
                self._lines.append(line.rstrip('\n'))      
        self._buffer = Buffer(self._lines)

    def run(self):
        # Save previous terminal file descriptor settings and start raw mode
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        try:
            tty.setraw(sys.stdin.fileno())
            # Main loop
            while 1:
                self.render()
                self.handle_input()
        # Return terminal to previous file descriptor settings
        finally:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def handle_input(self):
        # Get a single char input
        getch = _GetchUnix()
        char = getch()
        # Ctrl + Q : QUIT
        if char == chr(17):
            # Output QUIT with white fg color, red bg, and clear screen below then quit
            sys.stdout.write("\r\n\033[37;41m{}\033[39;49m\r\n\033[J".format("QUIT"))
            sys.exit(0)
        # Ctrl + U : UNDO
        elif char == chr(21):
            self.restore_snapshot()
        # Ctrl + H : MOVE CURSOR LEFT
        elif char == chr(8):
            self._cursor = self._cursor.left(self._buffer)
        # Ctrl + J : MOVE CURSOR DOWN
        elif char == chr(10):
            self._cursor = self._cursor.down(self._buffer)
            if self._cursor._row == shutil.get_terminal_size().lines - 2:
                self.scroll_down()
        # Ctrl + K : MOVE CURSOR UP
        elif char == chr(11):
            self._cursor = self._cursor.up(self._buffer)
            if self._cursor._row == 0:
                self.scroll_up()
        # Ctrl + L : MOVE CURSOR RIGHT
        elif char == chr(12):
            self._cursor = self._cursor.right(self._buffer)
        # Ctrl + E : SCROLL BUFFER DOWN
        elif char == chr(5):
            self.scroll_down()
        # Ctrl + Y : SCROLL BUFFER UP
        elif char == chr(25):
            self.scroll_up()
        # Tab key - Terminals see this as Ctrl + I, ASCII code 9
        elif char == chr(9):
            self._buffer = self._buffer.insert_tab_spaces(self._cursor._row, self._cursor._col)
            self._cursor = self._cursor.move_to_col(self._cursor._col + 4)
        # Return key
        elif char == "\r":
            self.save_snapshot()
            self._buffer = self._buffer.split_line(self._cursor._row, self._cursor._col)
            self._cursor = self._cursor.down(self._buffer).move_to_col(0)
        # Backspace key
        elif char == chr(127): 
            self.save_snapshot()
            if self._cursor._col > 0:
                self._buffer = self._buffer.delete(self._cursor._row, self._cursor._col - 1)
                self._cursor = self._cursor.left(self._buffer)
            elif self._cursor._col == 0 and self._cursor._row != 0:
                temp_cursor = self._cursor
                self._cursor = self._cursor.up(self._buffer).move_to_end(self._buffer)
                self._buffer = self._buffer.shift_line_up(temp_cursor._row)
        # Any other input:
        else:
            self.save_snapshot()
            self._buffer = self._buffer.insert(char, self._cursor._row, self._cursor._col) 
            self._cursor = self._cursor.right(self._buffer)
                    
    def render(self):
        ANSI.clear_screen()
        ANSI.move_cursor(0, 0)
        self._buffer.render(self._min_row, self._max_row, self._cursor)
        ANSI.move_cursor(self._cursor._row, self._cursor._col+3)
        # Cursor move is buffered if i dont do this :/
        sys.stdout.flush()

    def save_snapshot(self):
        self._history.append([self._buffer, self._cursor])

    def restore_snapshot(self): 
        if len(self._history):
            self._buffer, self._cursor = self._history.pop()

    def scroll_up(self):
        if self._min_row > 0:
            self._min_row -= 1
            self._max_row -= 1

    def scroll_down(self):
        if self._max_row < self._buffer.line_count:
            self._min_row += 1
            self._max_row += 1

class Buffer:
    def __init__(self, lines):
        self._lines = lines
    
    def render(self, min_row, max_row, cursor):
        for i in range(self.line_count):
            if i in range(min_row, max_row):
                if i == cursor._row:
                    # TODO dynamically format the leading 0's based on line count
                    print("\033[37;42m{num:02d}\033[39;49m ".format(num = i), end="")
                else:
                    # TODO dynamically format the leading 0's based on line count
                    print("\033[37;44m{num:02d}\033[39;49m ".format(num = i), end="")
                sys.stdout.write(self._lines[i] + "\r\n")
            #sys.stdout.flush() # Not required in raw mode apparently
    
    @property
    def line_count(self):
        return len(self._lines)
        
    def line_length(self, row):
        return len(self._lines[row])
        
    def insert(self, char, row, col):
        lines = copy.deepcopy(self._lines)
        # Insert the new char at the cursor position in the line
        lines[row] = lines[row][:col] + char + lines[row][col:]
        return Buffer(lines)
    
    def delete(self, row, col):
        lines = copy.deepcopy(self._lines)
        # delete the char at the cursor position in the line
        lines[row] = lines[row][:col] + lines[row][col+1:]
        return Buffer(lines)

    def split_line(self, row, col):
        lines = copy.deepcopy(self._lines)
        left_half = lines[row][:col]
        right_half = lines[row][col:]
        lines[row] = left_half
        lines.insert(row + 1, right_half)
        return Buffer(lines)

    def shift_line_up(self, row):
        lines = copy.deepcopy(self._lines)
        end_of_above_line = len(lines[row - 1]) + 1
        lines[row - 1] = lines[row - 1] + lines[row]
        del lines[row]
        return Buffer(lines)
    
    def insert_tab_spaces(self, row, col):
        lines = copy.deepcopy(self._lines)
        # Insert 4 spaces in place of the tab
        lines[row] = lines[row][:col] + "    " + lines[row][col:]
        return Buffer(lines)

class Cursor:
    def __init__(self, row = 0, col = 0):
        self._row = row
        self._col = col
    
    def left(self, buffer):
        return Cursor(self._row, self._col - 1).clamp(buffer)
    
    def down(self, buffer):
        return Cursor(self._row + 1, self._col).clamp(buffer)
        
    def up(self, buffer):
        return Cursor(self._row - 1, self._col).clamp(buffer)
        
    def right(self, buffer):
        return Cursor(self._row, self._col + 1).clamp(buffer)
    
    # Constrain cursor motion
    def clamp(self, buffer):
        bottom_row = shutil.get_terminal_size().lines - 2
        # Prevent cursor motion beyond the last line
        self._row = sorted((0, self._row, bottom_row))[1]
        # Prevent cursor motion beyond one space after the last char in a line
        self._col = sorted((0, self._col, buffer.line_length(self._row)))[1]
        return Cursor(self._row, self._col)
    
    def move_to_col(self, col):
        return Cursor(self._row, col)

    def move_to_end(self, buffer):
        return Cursor(self._row, buffer.line_length(self._row))

class ANSI:
    def clear_screen():
        sys.stdout.write("\033[2J")

    def move_cursor(row, col):
        sys.stdout.write("\033[{};{}H".format(row + 1, col + 1))

# Gets a single char input. Code copied from StackOverflow
class _GetchUnix:
    def __call__(self):
        ch = sys.stdin.read(1)
        return ch

e = Editor()
e.run()