# Actual cursor position and visual cursor position diverge
This happens in two slightly different cases.

1. Using ctrl+e and ctrl+y to scroll the screen up or down. The actual cursor never moves, but the visual one moves correctly.

2. By scrolling off the bottom of the screen using ctrl+j. The actual cursor again is always stuck at the bottom-most row, and the visual one correctly moves.

You can combine the two ways to also screw up the cursor. In every case, the visual cursor is always in the correct position.


# Lines that are wider than screen width go crazy (both visually and its contents)
it's borked, basically
