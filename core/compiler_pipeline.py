import os
import sys

# Allow direct execution/imports when cwd is `core/`.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ai.ai_optimizer import AIOptimizer
from optimizer.algorithm_detector import detect_algorithm
from optimizer.complexity import estimate_complexity
from optimizer.constant_folding import fold_constants
from optimizer.dead_code_elimination import remove_dead_code
from optimizer.loop_optimizer import optimize_loops
from optimizer.memory_optimizer import optimize_memory


class CompilerPipeline:
    def __init__(self):
        self.ai = AIOptimizer()

    def run(self, code):
        optimized = fold_constants(code)
        optimized = remove_dead_code(optimized)
        optimized = optimize_loops(optimized)
        optimized = optimize_memory(optimized)
        return optimized

    def optimize(self, code):
        optimized = self.run(code)
        return {
            "optimized_code": optimized,
            "algorithm": detect_algorithm(optimized),
            "complexity": estimate_complexity(optimized),
            "ai_suggestions": self.ai.suggest(optimized),
        }
