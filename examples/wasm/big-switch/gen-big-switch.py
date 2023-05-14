#!/usr/bin/env python3
N = 1000

print("""
int main(int argc, char **argv) {
\tint sum = 0;
\tfor (int i = 0; i < 10; ++i) {
\t\tswitch (argc) {""")

for i in range(N):
    print(f"\t\t\tcase {i}: sum += {N - i} + i;")
    
print("\t\t}")
print("""\t}
\treturn sum % 100;
}""")
