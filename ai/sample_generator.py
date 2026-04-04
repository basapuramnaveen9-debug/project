import random

from core.languages import normalize_language


def _c_dead_block(target_name):
    return f"""  if (0) {{
    {target_name} = {target_name} + 1000;
    for (int k = 0; k < 1; k++) {target_name} += k;
  }}
"""


def _cpp_dead_block(target_name):
    return f"""  if (false) {{
    {target_name} = {target_name} + 1000;
    for (int k = 0; k < 1; k++) {target_name} += k;
  }}
"""


def _java_dead_block(target_name):
    return f"""    if (false) {{
      {target_name} = {target_name} + 1000;
      for (int k = 0; k < 1; k++) {target_name} += k;
    }}
"""


def _python_dead_block(target_name):
    return f"""if False:
    {target_name} = {target_name} + 1000
    for _ in range(1):
        {target_name} += 1
"""


def _format_c_array(values):
    return "{ " + ", ".join(str(value) for value in values) + " }"


def _format_c_matrix(matrix):
    rows = ", ".join("{ " + ", ".join(str(value) for value in row) + " }" for row in matrix)
    return "{ " + rows + " }"


def _format_java_array(values):
    return "{ " + ", ".join(str(value) for value in values) + " }"


def _format_java_matrix(matrix):
    rows = ", ".join("{ " + ", ".join(str(value) for value in row) + " }" for row in matrix)
    return "{ " + rows + " }"


def _format_python_array(values):
    return "[" + ", ".join(str(value) for value in values) + "]"


def _format_python_matrix(matrix):
    rows = ", ".join("[" + ", ".join(str(value) for value in row) + "]" for row in matrix)
    return "[" + rows + "]"


_nested_sizes = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
_nested_factors = [2, 3, 4, 5, 6, 3, 4, 5, 6, 7]
_nested_offsets = [4, 6, 8, 10, 12, 14, 16, 18, 20, 22]

NESTED_SUM_SPECS = [
    {"kind": "nested_sum", "size": size, "factor": factor, "offset": offset}
    for size, factor, offset in zip(_nested_sizes, _nested_factors, _nested_offsets)
]

PRIME_SCAN_SPECS = [
    {"kind": "prime_scan", "limit": limit}
    for limit in [20, 25, 30, 35, 40, 45, 50, 55, 60, 65]
]

STRING_SCAN_SPECS = [
    {"kind": "string_scan", "word": word}
    for word in [
        "optimization",
        "parallelism",
        "complexity",
        "execution",
        "throughput",
        "latency",
        "pipeline",
        "debugging",
        "refactor",
        "analysis",
    ]
]

ARRAY_STATS_SPECS = [
    {"kind": "array_stats", "values": [3, 7, 2, 9, 4, 6], "threshold": 5},
    {"kind": "array_stats", "values": [10, 5, 8, 3, 1, 12, 7], "threshold": 6},
    {"kind": "array_stats", "values": [2, 4, 6, 8, 10], "threshold": 7},
    {"kind": "array_stats", "values": [9, 1, 4, 7, 2, 5, 8], "threshold": 4},
    {"kind": "array_stats", "values": [11, 3, 5, 7, 9, 2], "threshold": 8},
    {"kind": "array_stats", "values": [6, 14, 2, 9, 11, 5], "threshold": 10},
    {"kind": "array_stats", "values": [8, 3, 12, 4, 7, 1, 9], "threshold": 6},
    {"kind": "array_stats", "values": [5, 15, 10, 2, 6, 13], "threshold": 9},
    {"kind": "array_stats", "values": [7, 4, 9, 1, 8, 2, 6], "threshold": 5},
    {"kind": "array_stats", "values": [12, 6, 3, 9, 15, 2, 8], "threshold": 7},
]

SEARCH_VALUE_SPECS = [
    {"kind": "search_value", "values": [4, 7, 1, 9, 2, 5], "target": 9},
    {"kind": "search_value", "values": [13, 8, 5, 3, 6], "target": 10},
    {"kind": "search_value", "values": [2, 2, 2, 3, 4], "target": 3},
    {"kind": "search_value", "values": [15, 12, 9, 6, 3], "target": 12},
    {"kind": "search_value", "values": [1, 4, 9, 16, 25], "target": 16},
    {"kind": "search_value", "values": [5, 11, 7, 3, 9, 2], "target": 7},
    {"kind": "search_value", "values": [14, 6, 10, 2, 8], "target": 5},
    {"kind": "search_value", "values": [21, 18, 15, 12, 9], "target": 18},
    {"kind": "search_value", "values": [3, 6, 9, 12, 15], "target": 6},
    {"kind": "search_value", "values": [8, 1, 4, 6, 10, 12], "target": 1},
]

MATRIX_DIAG_SPECS = [
    {"kind": "matrix_diag", "matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]},
    {"kind": "matrix_diag", "matrix": [[2, 1, 0], [3, 5, 7], [8, 6, 4]]},
    {"kind": "matrix_diag", "matrix": [[9, 8, 7], [6, 5, 4], [3, 2, 1]]},
    {"kind": "matrix_diag", "matrix": [[5, 0, 2], [1, 3, 4], [6, 7, 8]]},
    {"kind": "matrix_diag", "matrix": [[4, 6, 8], [2, 5, 7], [1, 3, 9]]},
    {"kind": "matrix_diag", "matrix": [[7, 2, 5], [9, 1, 3], [4, 6, 8]]},
    {"kind": "matrix_diag", "matrix": [[8, 4, 6], [2, 7, 1], [5, 3, 9]]},
    {"kind": "matrix_diag", "matrix": [[3, 5, 7], [1, 9, 2], [6, 4, 8]]},
    {"kind": "matrix_diag", "matrix": [[6, 1, 4], [8, 2, 9], [3, 5, 7]]},
    {"kind": "matrix_diag", "matrix": [[9, 3, 1], [4, 8, 6], [2, 7, 5]]},
]

SAMPLE_SPECS = (
    NESTED_SUM_SPECS
    + PRIME_SCAN_SPECS
    + STRING_SCAN_SPECS
    + ARRAY_STATS_SPECS
    + SEARCH_VALUE_SPECS
    + MATRIX_DIAG_SPECS
)

_SAMPLE_POOLS = {}


def _next_spec(language):
    pool = _SAMPLE_POOLS.get(language)
    if not pool:
        pool = list(SAMPLE_SPECS)
        random.shuffle(pool)
        _SAMPLE_POOLS[language] = pool
    return pool.pop()


def _build_c_nested_sum(spec):
    size = spec["size"]
    factor = spec["factor"]
    offset = spec["offset"]
    dead_block = _c_dead_block("sum")
    return f"""#include <stdio.h>

int main(void) {{
  int n = {size};
  int sum = 0;
  int factor = {factor};
  int base = 2 + 3;
  int offset = {offset} + 0;

  for (int i = 0; i < n; i++) {{
    for (int j = 0; j < n; j++) {{
      int repeated = factor * 10;
      sum += i + j + repeated + base + offset;
    }}
  }}

{dead_block}  printf("sum = %d\\n", sum);
  return 0;
}}"""


def _build_c_prime_scan(spec):
    limit = spec["limit"]
    dead_block = _c_dead_block("printed")
    return f"""#include <stdio.h>

int main(void) {{
  int limit = {limit};
  int printed = 0;
  int constant_flag = 1 + 0;

  for (int n = 2; n <= limit; n++) {{
    int is_prime = 1;

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

{dead_block}  printf("\\ncount = %d\\n", printed);
  return 0;
}}"""


def _build_c_string_scan(spec):
    word = spec["word"]
    dead_block = _c_dead_block("vowels")
    return f"""#include <ctype.h>
#include <stdio.h>
#include <string.h>

int main(void) {{
  char text[] = "{word}";
  int vowels = 0;
  int extra = 8 * 4;

  for (int i = 0; i < (int)strlen(text); i++) {{
    char ch = (char) tolower((unsigned char) text[i]);
    if (ch == 'a' || ch == 'e' || ch == 'i' || ch == 'o' || ch == 'u') {{
      vowels++;
    }}
  }}

{dead_block}  printf("vowels = %d, extra = %d\\n", vowels, extra);
  return 0;
}}"""


def _build_c_array_stats(spec):
    values = spec["values"]
    threshold = spec["threshold"]
    array_literal = _format_c_array(values)
    dead_block = _c_dead_block("sum")
    return f"""#include <stdio.h>

int main(void) {{
  int values[] = {array_literal};
  int count = (int)(sizeof(values) / sizeof(values[0]));
  int threshold = {threshold} + 0;
  int sum = 0;
  int above = 0;
  int scale = 6 / 2;

  for (int i = 0; i < count; i++) {{
    sum += values[i] * scale;
    if (values[i] > threshold) {{
      above++;
    }}
  }}

{dead_block}  printf("sum = %d, above = %d\\n", sum, above);
  return 0;
}}"""


def _build_c_search_value(spec):
    values = spec["values"]
    target = spec["target"]
    array_literal = _format_c_array(values)
    dead_block = _c_dead_block("found")
    return f"""#include <stdio.h>

int main(void) {{
  int values[] = {array_literal};
  int count = (int)(sizeof(values) / sizeof(values[0]));
  int target = {target} + 0;
  int found = 0;

  for (int i = 0; i < count; i++) {{
    if (values[i] == target) {{
      found = 1;
      break;
    }}
  }}

{dead_block}  printf("found = %d\\n", found);
  return 0;
}}"""


def _build_c_matrix_diag(spec):
    matrix = spec["matrix"]
    matrix_literal = _format_c_matrix(matrix)
    size = len(matrix)
    dead_block = _c_dead_block("sum")
    return f"""#include <stdio.h>

int main(void) {{
  int matrix[{size}][{size}] = {matrix_literal};
  int n = {size} + 0;
  int sum = 0;
  int base = 3 + 1;

  for (int i = 0; i < n; i++) {{
    sum += matrix[i][i] + base;
  }}

{dead_block}  printf("diag = %d\\n", sum);
  return 0;
}}"""


def _build_cpp_nested_sum(spec):
    size = spec["size"]
    factor = spec["factor"]
    offset = spec["offset"]
    dead_block = _cpp_dead_block("sum")
    return f"""#include <iostream>

int main() {{
  int n = {size};
  int sum = 0;
  int factor = {factor};
  int base = 2 + 3;
  int offset = {offset} + 0;

  for (int i = 0; i < n; i++) {{
    for (int j = 0; j < n; j++) {{
      int repeated = factor * 10;
      sum += i + j + repeated + base + offset;
    }}
  }}

{dead_block}  std::cout << "sum = " << sum << "\\n";
  return 0;
}}"""


def _build_cpp_prime_scan(spec):
    limit = spec["limit"]
    dead_block = _cpp_dead_block("printed")
    return f"""#include <iostream>

int main() {{
  int limit = {limit};
  int printed = 0;
  int constant_flag = 1 + 0;

  for (int n = 2; n <= limit; n++) {{
    int is_prime = 1;

    for (int i = 2; i < n; i++) {{
      if (n % i == 0) {{
        is_prime = 0;
      }}
    }}

    if (is_prime && constant_flag) {{
      std::cout << n << " ";
      printed++;
    }}
  }}

{dead_block}  std::cout << "\\ncount = " << printed << "\\n";
  return 0;
}}"""


def _build_cpp_string_scan(spec):
    word = spec["word"]
    dead_block = _cpp_dead_block("vowels")
    return f"""#include <cctype>
#include <iostream>
#include <string>

int main() {{
  std::string text = "{word}";
  int vowels = 0;
  int extra = 8 * 4;

  for (char ch : text) {{
    char lower = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    if (lower == 'a' || lower == 'e' || lower == 'i' || lower == 'o' || lower == 'u') {{
      vowels++;
    }}
  }}

{dead_block}  std::cout << "vowels = " << vowels << ", extra = " << extra << "\\n";
  return 0;
}}"""


def _build_cpp_array_stats(spec):
    values = spec["values"]
    threshold = spec["threshold"]
    array_literal = _format_c_array(values)
    dead_block = _cpp_dead_block("sum")
    return f"""#include <iostream>

int main() {{
  int values[] = {array_literal};
  int count = (int)(sizeof(values) / sizeof(values[0]));
  int threshold = {threshold} + 0;
  int sum = 0;
  int above = 0;
  int scale = 6 / 2;

  for (int i = 0; i < count; i++) {{
    sum += values[i] * scale;
    if (values[i] > threshold) {{
      above++;
    }}
  }}

{dead_block}  std::cout << "sum = " << sum << ", above = " << above << "\\n";
  return 0;
}}"""


def _build_cpp_search_value(spec):
    values = spec["values"]
    target = spec["target"]
    array_literal = _format_c_array(values)
    dead_block = _cpp_dead_block("found")
    return f"""#include <iostream>

int main() {{
  int values[] = {array_literal};
  int count = (int)(sizeof(values) / sizeof(values[0]));
  int target = {target} + 0;
  int found = 0;

  for (int i = 0; i < count; i++) {{
    if (values[i] == target) {{
      found = 1;
      break;
    }}
  }}

{dead_block}  std::cout << "found = " << found << "\\n";
  return 0;
}}"""


def _build_cpp_matrix_diag(spec):
    matrix = spec["matrix"]
    matrix_literal = _format_c_matrix(matrix)
    size = len(matrix)
    dead_block = _cpp_dead_block("sum")
    return f"""#include <iostream>

int main() {{
  int matrix[{size}][{size}] = {matrix_literal};
  int n = {size} + 0;
  int sum = 0;
  int base = 3 + 1;

  for (int i = 0; i < n; i++) {{
    sum += matrix[i][i] + base;
  }}

{dead_block}  std::cout << "diag = " << sum << "\\n";
  return 0;
}}"""


def _build_java_nested_sum(spec):
    size = spec["size"]
    factor = spec["factor"]
    offset = spec["offset"]
    dead_block = _java_dead_block("sum")
    return f"""public class Main {{
  public static void main(String[] args) {{
    int n = {size};
    int sum = 0;
    int factor = {factor};
    int base = 2 + 3;
    int offset = {offset} + 0;

    for (int i = 0; i < n; i++) {{
      for (int j = 0; j < n; j++) {{
        int repeated = factor * 10;
        sum += i + j + repeated + base + offset;
      }}
    }}

{dead_block}    System.out.println("sum = " + sum);
  }}
}}"""


def _build_java_prime_scan(spec):
    limit = spec["limit"]
    dead_block = _java_dead_block("printed")
    return f"""public class Main {{
  public static void main(String[] args) {{
    int limit = {limit};
    int printed = 0;
    int constantFlag = 1 + 0;

    for (int n = 2; n <= limit; n++) {{
      int isPrime = 1;

      for (int i = 2; i < n; i++) {{
        if (n % i == 0) {{
          isPrime = 0;
        }}
      }}

      if (isPrime == 1 && constantFlag == 1) {{
        System.out.print(n + " ");
        printed++;
      }}
    }}

{dead_block}    System.out.println("\\ncount = " + printed);
  }}
}}"""


def _build_java_string_scan(spec):
    word = spec["word"]
    dead_block = _java_dead_block("vowels")
    return f"""public class Main {{
  public static void main(String[] args) {{
    String text = "{word}";
    int vowels = 0;
    int extra = 8 * 4;

    for (int i = 0; i < text.length(); i++) {{
      char ch = Character.toLowerCase(text.charAt(i));
      if (ch == 'a' || ch == 'e' || ch == 'i' || ch == 'o' || ch == 'u') {{
        vowels++;
      }}
    }}

{dead_block}    System.out.println("vowels = " + vowels + ", extra = " + extra);
  }}
}}"""


def _build_java_array_stats(spec):
    values = spec["values"]
    threshold = spec["threshold"]
    array_literal = _format_java_array(values)
    dead_block = _java_dead_block("sum")
    return f"""public class Main {{
  public static void main(String[] args) {{
    int[] values = {array_literal};
    int count = values.length;
    int threshold = {threshold} + 0;
    int sum = 0;
    int above = 0;
    int scale = 6 / 2;

    for (int i = 0; i < count; i++) {{
      sum += values[i] * scale;
      if (values[i] > threshold) {{
        above++;
      }}
    }}

{dead_block}    System.out.println("sum = " + sum + ", above = " + above);
  }}
}}"""


def _build_java_search_value(spec):
    values = spec["values"]
    target = spec["target"]
    array_literal = _format_java_array(values)
    dead_block = _java_dead_block("found")
    return f"""public class Main {{
  public static void main(String[] args) {{
    int[] values = {array_literal};
    int count = values.length;
    int target = {target} + 0;
    int found = 0;

    for (int i = 0; i < count; i++) {{
      if (values[i] == target) {{
        found = 1;
        break;
      }}
    }}

{dead_block}    System.out.println("found = " + found);
  }}
}}"""


def _build_java_matrix_diag(spec):
    matrix = spec["matrix"]
    matrix_literal = _format_java_matrix(matrix)
    size = len(matrix)
    dead_block = _java_dead_block("sum")
    return f"""public class Main {{
  public static void main(String[] args) {{
    int[][] matrix = {matrix_literal};
    int n = {size} + 0;
    int sum = 0;
    int base = 3 + 1;

    for (int i = 0; i < n; i++) {{
      sum += matrix[i][i] + base;
    }}

{dead_block}    System.out.println("diag = " + sum);
  }}
}}"""


def _build_python_nested_sum(spec):
    size = spec["size"]
    factor = spec["factor"]
    offset = spec["offset"]
    dead_block = _python_dead_block("sum_value")
    return f"""n = {size}
sum_value = 0
factor = {factor}
base = 2 + 3
offset = {offset} + 0

for i in range(n):
    for j in range(n):
        repeated = factor * 10
        sum_value += i + j + repeated + base + offset

{dead_block}print(f"sum = {{sum_value}}")
"""


def _build_python_prime_scan(spec):
    limit = spec["limit"]
    dead_block = _python_dead_block("printed")
    return f"""limit = {limit}
printed = 0
constant_flag = 1 + 0
values = []

for n in range(2, limit + 1):
    is_prime = True

    for i in range(2, n):
        if n % i == 0:
            is_prime = False

    if is_prime and constant_flag:
        values.append(str(n))
        printed += 1

{dead_block}print(" ".join(values))
print(f"count = {{printed}}")
"""


def _build_python_string_scan(spec):
    word = spec["word"]
    dead_block = _python_dead_block("vowels")
    return f"""text = "{word}"
vowels = 0
extra = 8 * 4

for ch in text:
    lower = ch.lower()
    if lower in "aeiou":
        vowels += 1

{dead_block}print(f"vowels = {{vowels}}, extra = {{extra}}")
"""


def _build_python_array_stats(spec):
    values = spec["values"]
    threshold = spec["threshold"]
    array_literal = _format_python_array(values)
    dead_block = _python_dead_block("sum_value")
    return f"""values = {array_literal}
threshold = {threshold} + 0
sum_value = 0
above = 0
scale = 6 // 2

for value in values:
    sum_value += value * scale
    if value > threshold:
        above += 1

{dead_block}print(f"sum = {{sum_value}}, above = {{above}}")
"""


def _build_python_search_value(spec):
    values = spec["values"]
    target = spec["target"]
    array_literal = _format_python_array(values)
    dead_block = _python_dead_block("found")
    return f"""values = {array_literal}
target = {target} + 0
found = 0
scale = 2 + 3

for value in values:
    if value == target:
        found = scale
        break

{dead_block}print(f"found = {{found}}")
"""


def _build_python_matrix_diag(spec):
    matrix = spec["matrix"]
    matrix_literal = _format_python_matrix(matrix)
    size = len(matrix)
    dead_block = _python_dead_block("sum_value")
    return f"""matrix = {matrix_literal}
n = {size} + 0
sum_value = 0
base = 3 + 1

for i in range(n):
    sum_value += matrix[i][i] + base

{dead_block}print(f"diag = {{sum_value}}")
"""


LANGUAGE_BUILDERS = {
    "c": {
        "nested_sum": _build_c_nested_sum,
        "prime_scan": _build_c_prime_scan,
        "string_scan": _build_c_string_scan,
        "array_stats": _build_c_array_stats,
        "search_value": _build_c_search_value,
        "matrix_diag": _build_c_matrix_diag,
    },
    "cpp": {
        "nested_sum": _build_cpp_nested_sum,
        "prime_scan": _build_cpp_prime_scan,
        "string_scan": _build_cpp_string_scan,
        "array_stats": _build_cpp_array_stats,
        "search_value": _build_cpp_search_value,
        "matrix_diag": _build_cpp_matrix_diag,
    },
    "java": {
        "nested_sum": _build_java_nested_sum,
        "prime_scan": _build_java_prime_scan,
        "string_scan": _build_java_string_scan,
        "array_stats": _build_java_array_stats,
        "search_value": _build_java_search_value,
        "matrix_diag": _build_java_matrix_diag,
    },
    "python": {
        "nested_sum": _build_python_nested_sum,
        "prime_scan": _build_python_prime_scan,
        "string_scan": _build_python_string_scan,
        "array_stats": _build_python_array_stats,
        "search_value": _build_python_search_value,
        "matrix_diag": _build_python_matrix_diag,
    },
}

EXTRA_LANGUAGE_SAMPLES = {
    "javascript": """const values = [3, 7, 2, 9, 4];
let sum = 0;

if (false) {
  sum += 1000;
}

for (const value of values) {
  sum += value;
}

console.log(sum);
""",
    "typescript": """const values: number[] = [3, 7, 2, 9, 4];
let sum = 0;

if (false) {
  sum += 1000;
}

for (const value of values) {
  sum += value;
}

console.log(sum);
""",
    "go": """package main

import "fmt"

func main() {
    values := []int{3, 7, 2, 9, 4}
    sum := 0

    if false {
        sum += 1000
    }

    for _, value := range values {
        sum += value
    }

    fmt.Println(sum)
}
""",
    "rust": """fn main() {
    let values = [3, 7, 2, 9, 4];
    let mut sum = 0;

    if false {
        sum += 1000;
    }

    for value in values {
        sum += value;
    }

    println!("{}", sum);
}
""",
    "csharp": """using System;

class Program
{
    static void Main()
    {
        int[] values = { 3, 7, 2, 9, 4 };
        int sum = 0;

        if (false)
        {
            sum += 1000;
        }

        foreach (int value in values)
        {
            sum += value;
        }

        Console.WriteLine(sum);
    }
}
""",
    "php": """<?php
$values = [3, 7, 2, 9, 4];
$sum = 0;

if (false) {
    $sum += 1000;
}

foreach ($values as $value) {
    $sum += $value;
}

echo $sum . PHP_EOL;
""",
    "ruby": """values = [3, 7, 2, 9, 4]
sum = 0

if false
  sum += 1000
end

values.each do |value|
  sum += value
end

puts sum
""",
    "kotlin": """fun main() {
    val values = intArrayOf(3, 7, 2, 9, 4)
    var sum = 0

    if (false) {
        sum += 1000
    }

    for (value in values) {
        sum += value
    }

    println(sum)
}
""",
}


def generate_sample_program(language="c"):
    language = normalize_language(language)
    if language in EXTRA_LANGUAGE_SAMPLES:
        return EXTRA_LANGUAGE_SAMPLES[language]
    spec = _next_spec(language)
    builder = LANGUAGE_BUILDERS[language][spec["kind"]]
    return builder(spec)
