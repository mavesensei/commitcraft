def estimate_tokens(text: str) -> int:
    # Rough approximation: 1 token ≈ 4 characters (widely used heuristic)
    return max(1, len(text) // 4)
