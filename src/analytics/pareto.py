"""Dominance comparisons only among complete, finite objective vectors."""
import numpy as np


def pareto_evidence(objectives):
    matrix = np.asarray(objectives, dtype=float)
    complete = np.isfinite(matrix).all(axis=1)
    ranks = np.full(len(matrix), np.nan)
    for i in np.flatnonzero(complete):
        ranks[i] = 1 + sum(np.all(matrix[j] >= matrix[i]) and np.any(matrix[j] > matrix[i])
                           for j in np.flatnonzero(complete) if j != i)
    return complete, ranks
