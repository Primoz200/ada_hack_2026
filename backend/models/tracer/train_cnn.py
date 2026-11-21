"""1D-CNN on the time-resampled sequence (features.SEQ_CHANNELS @ 50 Hz) + level embedding -> score 0-100.

Variable-length attempts: batches are zero-padded and pooling is masked, so padding never counts.
Global pooling forgets the length of the attempt, so time_ratio (duration / time limit) and
`completed` go in as scalars next to the level embedding.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from common import report
from dataset import DATA, load
from features import SEQ_CHANNELS

ART = Path(__file__).resolve().parent / "artifacts"


class TracerCNN(nn.Module):
    def __init__(self, in_ch=len(SEQ_CHANNELS), width=64, n_levels=3, level_dim=8, dropout=0.1):
        super().__init__()
        chans = [in_ch, width // 2, width, width, 2 * width, 2 * width]
        layers = []
        for i, (a, b) in enumerate(zip(chans[:-1], chans[1:])):
            stride = 1 if i == 0 else 2  # 50 Hz -> ~3 Hz after 4 stride-2 blocks
            layers += [nn.Conv1d(a, b, 7, stride=stride, padding=3), nn.BatchNorm1d(b), nn.GELU()]
            if i > 0:
                layers.append(nn.Dropout1d(dropout))  # drops whole channels: stronger than per-value dropout
        self.conv = nn.Sequential(*layers)
        self.n_stride = 4
        self.level_emb = nn.Embedding(n_levels, level_dim)
        hidden = max(16, width)
        self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(4 * width + level_dim + 2, hidden), nn.GELU(),
                                  nn.Dropout(dropout), nn.Linear(hidden, 1))

    def forward(self, seq, mask, level, scalars):
        """seq [B, C, T], mask [B, T] (1 = real), level [B] (1-3), scalars [B, 2] -> score [B] in 0-100."""
        h = self.conv(seq * mask[:, None])
        m = mask[:, None]
        for _ in range(self.n_stride):
            m = F.max_pool1d(m, 7, stride=2, padding=3)
        m = m[..., : h.shape[-1]]
        mean = (h * m).sum(-1) / m.sum(-1).clamp(min=1)
        mx = h.masked_fill(m == 0, -1e4).amax(-1)
        z = torch.cat([mean, mx, self.level_emb(level - 1), scalars], dim=1)
        return 100 * torch.sigmoid(self.head(z).squeeze(1))


def make_batch(d, idx, device):
    off = d["seq_off"]
    lens = off[idx + 1] - off[idx]
    T = int(lens.max())
    seq = np.zeros((len(idx), len(SEQ_CHANNELS), T), np.float32)
    mask = np.zeros((len(idx), T), np.float32)
    for k, (i, n) in enumerate(zip(idx, lens)):
        seq[k, :, :n] = d["seq_flat"][off[i]:off[i + 1]].T
        mask[k, :n] = 1
    scal = np.column_stack([d["time_ratio"][idx], d["completed"][idx]]).astype(np.float32)
    t = lambda a, dt=torch.float32: torch.as_tensor(a, dtype=dt, device=device)
    return t(seq), t(mask), t(d["level"][idx], torch.long), t(scal), t(d["y"][idx])


def batches(d, idx, bs, shuffle, rng):
    """Bucket by length so padding stays small."""
    off = d["seq_off"]
    lens = off[idx + 1] - off[idx]
    order = idx[np.argsort(lens + (rng.uniform(0, 200, len(idx)) if shuffle else 0))]
    chunks = [order[i:i + bs] for i in range(0, len(order), bs)]
    if shuffle:
        rng.shuffle(chunks)
    return chunks


@torch.no_grad()
def predict(model, d, idx, device, bs=128):
    model.eval()
    out = np.zeros(len(idx), np.float32)
    pos = {i: k for k, i in enumerate(idx)}
    for b in batches(d, idx, bs, False, None):
        seq, mask, lv, sc, _ = make_batch(d, b, device)
        p = model(seq, mask, lv, sc).cpu().numpy()
        for i, v in zip(b, p):
            out[pos[i]] = v
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--bs", type=int, default=64)
    ap.add_argument("--lr", type=float, default=2e-3)
    ap.add_argument("--width", type=int, default=64)
    ap.add_argument("--dropout", type=float, default=0.1)
    ap.add_argument("--wd", type=float, default=1e-3, help="AdamW weight decay")
    ap.add_argument("--tag", default="", help="suffix for the history file (experiments)")
    args = ap.parse_args()

    torch.manual_seed(0)
    rng = np.random.default_rng(0)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    d = load()
    tr, va, te = (np.nonzero(d["split"] == k)[0] for k in (0, 1, 2))
    model = TracerCNN(width=args.width, dropout=args.dropout).to(device)
    print(f"device {device}, params {sum(p.numel() for p in model.parameters()):,}, train {len(tr)}")
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.wd)
    steps = args.epochs * len(batches(d, tr, args.bs, True, rng))
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=args.lr, total_steps=steps)

    best, best_state, history = 1e9, None, []
    for ep in range(args.epochs):
        model.train()
        t0, tot, n = time.time(), 0.0, 0
        for b in batches(d, tr, args.bs, True, rng):
            seq, mask, lv, sc, y = make_batch(d, b, device)
            loss = F.smooth_l1_loss(model(seq, mask, lv, sc), y, beta=5.0)
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            tot += loss.item() * len(b)
            n += len(b)
        val_mae = float(np.abs(predict(model, d, va, device) - d["y_clean"][va]).mean())
        train_mae = float(np.abs(predict(model, d, tr, device) - d["y"][tr]).mean())  # eval mode, noisy labels
        history.append({"epoch": ep + 1, "loss": tot / n, "train_mae": train_mae, "val_mae": val_mae})
        if val_mae < best:
            best, best_state = val_mae, {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        print(f"epoch {ep + 1:3d}  loss {tot / n:6.2f}  train MAE(noisy) {train_mae:5.2f}  "
              f"val MAE(clean) {val_mae:5.2f}  {time.time() - t0:4.1f}s", flush=True)

    model.load_state_dict(best_state)
    n_params = sum(p.numel() for p in model.parameters())
    results = {}
    for name, idx in (("val", va), ("test", te)):
        pred = predict(model, d, idx, device)
        results[name] = report(f"CNN {name}", pred, d["y"][idx], d["y_clean"][idx], d["level"][idx])
    test_pred = predict(model, d, te, device)

    DATA.mkdir(exist_ok=True)
    hist_file = DATA / f"cnn_history{('_' + args.tag) if args.tag else ''}.json"
    hist_file.write_text(json.dumps({"args": vars(args), "params": n_params, "history": history, "results": results,
                                     "test_pred": test_pred.round(2).tolist()}))
    print(f"history -> {hist_file}")
    if not args.tag:  # experiments (--tag) do not overwrite the deployed model
        ART.mkdir(exist_ok=True)
        torch.save({"state_dict": best_state, "config": {"width": args.width, "dropout": args.dropout},
                    "seq_channels": SEQ_CHANNELS, "version": "tracer-cnn-0.2"}, ART / "tracer_cnn.pt")
        print(f"saved {ART / 'tracer_cnn.pt'}")


if __name__ == "__main__":
    main()
