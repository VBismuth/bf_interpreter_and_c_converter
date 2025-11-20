[
Introduction

I wanted to write a simple demonstration program to test the performance of brainfuck interpreters. To this end, I wanted a program that does not halt, does not repeat a state, and does not use much memory. The program must not halt because the purpose is to test how fast a brainfuck interpreter can execute a non-terminating program. The program should not repeat a state because if it did, the state would not adequately prove that a certain amount of computation was performed. And the program should not use much memory, because it would stress the host’s memory allocation system and could potentially acquire (and never release) memory at megabytes per second.

Writing an example of a halting program in brainfuck is easy: just don’t use any loops. Writing a non-halting program that does not repeat a state is also easy: +[>+]. This program loops infinitely, incrementing a cell and moving right. It consumes memory at a rate linear to the number of steps executed, which is too fast for my purposes. So I thought of writing a binary counter, which never repeats a state but consumes memory at a rate logarithmic to the number of steps executed. But as I quickly learned, writing programs in brainfuck to accomplish typical computations is not easy. In fact, it forces the programmer to enter a twisted mode of thinking, twisted enough that the programming language really deserves the name brainfuck. In the rest of this article, I will step through how to write a binary counter in brainfuck and what challenges there are along the way.
Binary counter design process
0. Preliminary code

Let’s start by writing a snippet of code to implement a binary counter in a typical imperative language like C, Java, Python, etc. Assume that memory is an infinite array of unsigned bytes initialized to all zeros. We will use each array element as a binary digit, where memory[0] is the least significant digit (ones), memory[1] is the next least significant digit (twos), memory[2] is fours, memory[3] is eights, and so on. The code:

while (true) {
    memory[0]++;  // Increment the ones digit
    int i = 0;
    while (memory[i] == 2) {  // Do carries
        memory[i] = 0;
        memory[i+1]++;
        i++;
    }
}

1. Rewinding

The first problem we hit is that in each iteration of the outer loop, we modify the memory at index 0, then step to higher indices, then rewind back to index 0 for the next iteration. But brainfuck does not have absolute indexing! So, what we do is to write a special sentinel value just before the least significant digit, then search for it when we want to rewind. I choose to use the value 255 because it’s simply a decrement of 0.

So now, suppose memory[-1] = 255, and our current index is at least 0. How do we rewind back to index 0? Here is the obvious code:

while (memory[i] + 1 != 0)
    i--;

We transform the code by adding some temporary writes:

while (true) {
    memory[i]++;
    if (memory[i] == 0) {
        memory[i]--;
        break;
    }
    memory[i]--;
    i--;
}

And we move some code within the loop and out of the loop (you can visualize why this is correct by unrolling the loop):

memory[i]++;
while (memory[i] != 0) {
    memory[i]--;
    i--;
    memory[i]++;
}
memory[i]--;

This is the brainfuck code that we end up with: +[-<+]-
2. Incrementing

Our initial binary counter code increments a cell and sees if it overflows to 2, then performs a carry and repeats. As a functionally equivalent alternative, we can scan for consecutive 1s starting from the least significant digit, change them all to 0, and change the next immediate 0 into a 1. Code:

while (memory[i] != 0) {
    memory[i]--;
    i++;
}
memory[i]++;

Brainfuck code: [->]+.
3. Looping

Finally, we need to loop these iterations of incrementing and rewinding. To do that, we wrap everything we have so far in a loop. Then we make sure that the memory pointer is always at the sentinel value (leftmost cell) when doing the loop test, since it is always nonzero. Putting it all together, we finally get this code:


-          # Make leftmost cell as the sentinel, value 255
[          # Loop on the sentinel (which is nonzero)
  >        # Move to least significant bit
  [->]     # Zero out consecutive 1s going right
  +        # Now that we hit a 0, change it to 1
  +[-<+]-  # Move left until we hit a cell with value 255
]          # Now at the sentinel, repeat forever

Or expressed compactly: -[>[->]++[-<+]-]
Notes

Try it out on my brainfuck interpreter page!

A reader Joshua King contributed this alternative binary counter program: >+[[>]+<[-<]>+]. His code was created in May 2017, whereas my code is from Nov 2011. Joshua’s code is better than mine in every way: It is one character shorter, avoids decrementing any zero cell (a behavior that may differ across brainfuck implementations), and performs less work to update the counter (thus counts faster).
]
- [ >[->]+ +[-<+]- ]
