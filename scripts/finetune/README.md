# Fine-tuning laya-local commands

The base `laya-multilingual` checkpoint scores only ~40% zero-shot on
command intent classification. Fine-tuning on task data pushes that to
~77%+ (the official typed-decisions run: 0.766 vs 0.342 base).

## 1. Build the dataset

```bash
python scripts/finetune/dataset_builder.py --output data.jsonl
```

Generates ~1,000+ training items covering open/close app, open folder,
open URL, web search, system control, and media commands in English,
Malayalam, and Manglish.

Item schema (one JSON object per line):

```json
{
  "state": {"body": "chrome thurakku"},
  "questions": { ...standard command questions... },
  "targets": {
    "action": {"choice": "open_app"},
    "app_target": {"choice": "chrome"}
  }
}
```

## 2. Train (GPU required)

Use the **official Laya fine-tuning notebook** — it implements the full
RLCD / GRPO loop (2xT4, ~4-5 hours):

- https://github.com/NandhaKishorM/laya/blob/main/notebooks/laya_finetune_typed_decisions_2xT4_kaggle.ipynb
- Kaggle is free with 2xT4 GPUs.

Steps:

1. Open the notebook on Kaggle.
2. Replace its dataset cells with loading `data.jsonl` (the item schema
   is identical — `state` / `questions` / `targets`).
3. Run all cells. The notebook fits calibration temperatures, evaluates,
   and pushes the fine-tuned weights to your Hugging Face account.
4. Note the output repo id (e.g. `your-username/laya-commands`).

## 3. Use the fine-tuned model

Update `config.yaml`:

```yaml
laya:
  model: "your-username/laya-commands"
```

The `Classifier` already loads via `laya.load(model, subfolder="multilingual")`
— publish the fine-tuned multilingual checkpoint into that subfolder, or
adjust `core/classifier.py` if you retrain a different checkpoint layout.

## Notes

- Keep the fast-path `CommandMatcher` as-is: it handles the common case
  at 99% precision. Fine-tuning only improves the Laya fallback for
  novel phrasing.
- Add more command phrasings to `scripts/finetune/dataset_builder.py`
  and regenerate to cover your personal vocabulary.
- The `scripts/finetune/train.py` file is a scaffold documenting the
  entry point; the actual loop must run on GPU via the notebook.