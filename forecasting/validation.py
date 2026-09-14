"""Validation module for expanding-window chronological cross-validation."""
import numpy as np
import pandas as pd

def expanding_windows(n_rows, n_folds=5):
    """
    Return list of (train_end_index, val_end_index), chronological.
    Strictly past-to-future: train is [0:train_end], val is [train_end:val_end].
    """
    fold = n_rows // (n_folds + 1)
    if fold == 0:
        return []
    windows = []
    for i in range(n_folds):
        train_end = fold * (i + 1)
        val_end = fold * (i + 2) if i < n_folds - 1 else n_rows
        windows.append((train_end, val_end))
    return windows

def get_temporal_folds_by_date(df, date_col="year_month", n_folds=5):
    """
    Generate chronological train/val splits based on unique sorted dates.
    Ensures identical temporal cutoffs across all series.
    """
    unique_dates = sorted(df[date_col].unique())
    n_dates = len(unique_dates)
    windows = expanding_windows(n_dates, n_folds=n_folds)
    
    folds = []
    for fold_idx, (train_end_idx, val_end_idx) in enumerate(windows):
        train_dates = unique_dates[:train_end_idx]
        val_dates = unique_dates[train_end_idx:val_end_idx]
        
        train_mask = df[date_col].isin(train_dates)
        val_mask = df[date_col].isin(val_dates)
        
        folds.append({
            "fold": fold_idx,
            "train_dates": train_dates,
            "val_dates": val_dates,
            "train_mask": train_mask,
            "val_mask": val_mask,
            "train_indices": df.index[train_mask].to_numpy(),
            "val_indices": df.index[val_mask].to_numpy(),
        })
    return folds
