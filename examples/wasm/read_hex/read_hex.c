#include <stdio.h>

int main(void) 
{
    unsigned int value;
    int res = scanf("%x", &value);
    if (res != 1) {
        return -1;
    }
    
    return (value & 3u);
}
