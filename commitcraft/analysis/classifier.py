from dataclasses import dataclass, field
from pathlib import Path

from commitcraft.analysis.filters import FilteredDiff


@dataclass
class ClassificationResult:
    score: int
    is_simple: bool
    signals: dict[str, int | bool] = field(default_factory=dict)


def _count_directories(files: list) -> int:
    dirs = {str(Path(f.path).parent) for f in files}
    return len(dirs)


def _has_test_alongside_source(files: list) -> bool:
    paths = [f.path for f in files]
    has_test = any("test" in p.lower() for p in paths)
    has_source = any("test" not in p.lower() for p in paths)
    return has_test and has_source


def classify(filtered: FilteredDiff, threshold: int = 30) -> ClassificationResult:
    if not filtered.files:
        return ClassificationResult(score=0, is_simple=True, signals={
            "file_count": 0, "directory_spread": 0,
            "function_changes": 0, "test_alongside_source": False, "line_count": 0,
        })

    file_count = len(filtered.files)
    dir_spread = _count_directories(filtered.files)
    func_changes = sum(1 for f in filtered.files if f.has_function_changes or f.has_class_changes)
    test_with_source = _has_test_alongside_source(filtered.files)
    total_lines = filtered.total_added + filtered.total_removed

    # Weighted scoring (caps at 100)
    score = 0
    score += min(file_count * 5, 25)       # up to 25 pts for file count
    score += min(dir_spread * 5, 20)        # up to 20 pts for directory spread
    score += min(func_changes * 10, 30)     # up to 30 pts for function/class changes
    score += 10 if test_with_source else 0  # 10 pts for test+source together
    score += min(total_lines // 20, 15)     # up to 15 pts for line count

    score = min(score, 100)

    signals = {
        "file_count": file_count,
        "directory_spread": dir_spread,
        "function_changes": func_changes,
        "test_alongside_source": test_with_source,
        "line_count": total_lines,
    }

    return ClassificationResult(score=score, is_simple=score < threshold, signals=signals)
