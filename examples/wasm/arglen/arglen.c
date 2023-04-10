#include <stdio.h>
#include <string.h>

/* Assumes there are at least two command-line arguments. */
int main(int argc, char **argv) {
    int len = strlen(argv[1]);
    printf("%d\n", len);
    return 0;
}
