import random


def _common_dead_block(target_name):
    return f'''  if (0) {{
    {target_name} = {target_name} + 1000;
  }}

  while (0) {{
    {target_name}++;
  }}
'''


def _nested_sum_program():
    size = random.choice([4, 5, 6])
    factor = random.choice([2, 3, 4])
    dead_block = _common_dead_block("sum")
    return f'''#include <stdio.h>

int main(void) {{
  int n = {size};
  int sum = 0;
  int factor = {factor};
  int base = 2 + 3;
  int offset = 20 / 5;

  for (int i = 0; i < n; i++) {{
    for (int j = 0; j < n; j++) {{
      int repeated = factor * 10;
      sum += i + j + repeated + base + offset;
    }}
  }}

{dead_block}  printf("sum = %d\\n", sum);
  return 0;
}}'''


def _redundant_array_program():
    values = random.sample(range(5, 30), 6)
    values_text = ", ".join(str(v) for v in values)
    dead_block = _common_dead_block("sum")
    return f'''#include <stdio.h>

int main(void) {{
  int values[] = {{{values_text}}};
  int length = sizeof(values) / sizeof(values[0]);
  int sum = 0;
  int max = values[0];
  int average_scale = 100 / 5;

  for (int i = 0; i < length; i++) {{
    sum += values[i];
  }}

  for (int i = 0; i < length; i++) {{
    if (values[i] > max) {{
      max = values[i];
    }}
  }}

{dead_block}  printf("avg = %d, max = %d\\n", (sum / length) * average_scale, max);
  return 0;
}}'''


def _loop_io_program():
    count = random.choice([6, 8, 10])
    dead_block = _common_dead_block("total")
    return f'''#include <stdio.h>

int main(void) {{
  int total = 0;
  int bias = 3 * 7;

  for (int i = 0; i < {count}; i++) {{
    int value = i * i + bias;
    printf("value[%d] = %d\\n", i, value);
    total += value;
  }}

{dead_block}  printf("total = %d\\n", total);
  return 0;
}}'''


def _naive_prime_scan_program():
    limit = random.choice([20, 25, 30])
    return f'''#include <stdio.h>

int main(void) {{
  int limit = {limit};
  int printed = 0;

  for (int n = 2; n <= limit; n++) {{
    int is_prime = 1;
    int constant_flag = 1 + 0;

    for (int i = 2; i < n; i++) {{
      if (n % i == 0) {{
        is_prime = 0;
      }}
    }}

    if (is_prime && constant_flag) {{
      printf("%d ", n);
      printed++;
    }}
  }}

  if (0) {{
    printed = -1;
  }}

  printf("\\ncount = %d\\n", printed);
  return 0;
}}'''


def _string_scan_program():
    word = random.choice(["optimization", "parallelism", "complexity", "execution"])
    dead_block = _common_dead_block("vowels")
    return f'''#include <ctype.h>
#include <stdio.h>
#include <string.h>

int main(void) {{
  char text[] = "{word}";
  int vowels = 0;
  int extra = 8 * 4;

  for (int i = 0; i < strlen(text); i++) {{
    char ch = (char) tolower((unsigned char) text[i]);
    if (ch == 'a' || ch == 'e' || ch == 'i' || ch == 'o' || ch == 'u') {{
      vowels++;
    }}
  }}

{dead_block}  printf("vowels = %d, extra = %d\\n", vowels, extra);
  return 0;
}}'''


def _redundant_factorial_program():
    value = random.choice([5, 6, 7])
    return f'''#include <stdio.h>

long long factorial(int n) {{
  long long result = 1;
  for (int i = 1; i <= n; i++) {{
    result = result * i;
  }}
  return result;
}}

int main(void) {{
  int n = {value};
  long long first = factorial(n);
  long long second = factorial(n);
  int adjustment = 20 / 5;

  if (0) {{
    second = 0;
  }}

  printf("factorial = %lld, again = %lld, adjustment = %d\\n", first, second, adjustment);
  return 0;
}}'''


PROGRAM_BUILDERS = [
    _nested_sum_program,
    _redundant_array_program,
    _loop_io_program,
    _naive_prime_scan_program,
    _string_scan_program,
    _redundant_factorial_program,
]


def generate_sample_program():
    builder = random.choice(PROGRAM_BUILDERS)
    return builder()
