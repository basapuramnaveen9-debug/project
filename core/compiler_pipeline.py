import os
import sys

# Allow direct execution/imports when cwd is `core/`.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ai.ai_optimizer import AIOptimizer
from core.languages import normalize_language, supports_local_optimization
from optimizer.algorithm_detector import detect_algorithm
from optimizer.complexity import estimate_complexity
from optimizer.constant_folding import fold_constants
from optimizer.dead_code_elimination import remove_dead_code
from optimizer.loop_optimizer import optimize_loops
from optimizer.memory_optimizer import optimize_memory


def _count_non_empty_lines(code):
    return sum(1 for line in str(code or "").splitlines() if line.strip())


class CompilerPipeline:
    def __init__(self):
        self.ai = AIOptimizer()

    def run(self, code, language="c"):
        language = normalize_language(language)
        source = str(code or "")
        if not supports_local_optimization(language):
            return source

        optimized = fold_constants(code, language)
        optimized = remove_dead_code(optimized, language)
        optimized = optimize_loops(optimized, language)
        optimized = optimize_memory(optimized, language)
        optimized = str(optimized or "").strip()

        if not optimized:
            return source

        if _count_non_empty_lines(optimized) > _count_non_empty_lines(source):
            return source

        return optimized

    def optimize(self, code, language="c"):
        language = normalize_language(language)
        optimized = self.run(code, language)
        return {
            "optimized_code": optimized,
            "algorithm": detect_algorithm(optimized, language),
            "complexity": estimate_complexity(optimized, language),
            "ai_suggestions": self.ai.suggest(optimized, language),
        }
