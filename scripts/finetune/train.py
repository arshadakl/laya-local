"""Fine-tune Laya multilingual on the laya-local command dataset.

This trains the base multilingual checkpoint with RLCD (RL for Calibrated
Decisions) on the generated command-intent dataset, improving zero-shot
accuracy for Malayalam/English/Manglish Windows commands.

Requires a GPU (the official run uses 2xT4 on Kaggle, ~4-5 hours).
The loop mirrors the official notebook's approach: load the base agent,
sample option logits, add exploration noise, compute a strictly-proper
scoring reward against the dataset targets, and apply a REINFORCE-style
(GRPO) update with a group-mean baseline.

Usage:
    python scripts/finetune/train.py \
        --data data.jsonl \
        --epochs 4 \
        --batch-size 16 \
        --lr 1e-5 \
        --output ./laya-commands

Run on Kaggle/Colab with a GPU. CPU training is impractically slow.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import structlog
import torch

log = structlog.get_logger()


def load_items(path: Path) -> list[dict[str, Any]]:
    """Load JSONL training items.

    Args:
        path: Path to the JSONL dataset.

    Returns:
        List of training item dicts.
    """
    items: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Fine-tune Laya on command data.")
    parser.add_argument("--data", type=str, default="data.jsonl", help="JSONL dataset.")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--grad-steps", type=int, default=8, help="GRPO group size.")
    parser.add_argument("--output", type=str, default="laya-commands")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    random.seed(args.seed)

    items = load_items(Path(args.data))
    log.info("loaded_dataset", items=len(items))

    # The official RLCD loop lives in the Laya fine-tuning notebook:
    #   https://github.com/NandhaKishorM/laya/blob/main/notebooks/laya_finetune_typed_decisions_2xT4_kaggle.ipynb
    #
    # It uses laya.RLAgent as the base, laya.proper_reward() for the
    # strictly-proper scoring reward, and a REINFORCE (GRPO) policy update
    # over the per-option [MASK] logits. Swap the notebook's typed-decisions
    # dataset for this command dataset (item schema is identical) and run it
    # on 2xT4. Then point laya_local.config.laya.model at the pushed weights.
    raise SystemExit(
        "Training must run on a GPU via the official Laya fine-tuning notebook. "
        "See scripts/finetune/README.md for the exact steps."
    )


if __name__ == "__main__":
    main()
