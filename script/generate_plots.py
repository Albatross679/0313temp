"""
Generate all plots for the report.

Plots:
1. ICL sensitivity to k (Part 3)
2. Training curves for best T5-small FT and T5-base FT (Parts 1 & 2)
3. Dev F1 comparison bar chart across all T5 variants (Parts 1 & 2)
4. Fine-tuned vs. from-scratch learning dynamics (Parts 1 & 2)

Style: academic, serif fonts, appropriate for inclusion in a Palatino LaTeX document.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from script.training_curve_data import (
    ft_small_train_loss, ft_small_eval_metrics,
    ft_base_train_loss, ft_base_eval_metrics,
    scr_small_milestones, scr_small_late_f1,
)

# ── Style setup ──────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Palatino', 'Palatino Linotype', 'TeX Gyre Pagella', 'DejaVu Serif'],
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'axes.linewidth': 0.6,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linewidth': 0.4,
    'lines.linewidth': 1.2,
    'lines.markersize': 4,
})

MEDIA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'media')

# Colors - colorblind-friendly palette
C_FT_SMALL = '#2166ac'   # blue
C_FT_BASE  = '#b2182b'   # red
C_SCRATCH  = '#4daf4a'   # green
C_LOSS     = '#636363'   # gray
C_BM25     = '#2166ac'   # blue
C_RANDOM   = '#b2182b'   # red


# ════════════════════════════════════════════════════════════════
# Plot 1: ICL sensitivity to k
# ════════════════════════════════════════════════════════════════
def plot_icl_sensitivity():
    fig, ax = plt.subplots(figsize=(3.8, 2.6))

    # Data from the report
    k_random = [0, 1, 3]
    f1_random = [12.60, 12.60, 11.96]

    k_bm25 = [3]
    f1_bm25 = [17.35]

    ax.plot(k_random, f1_random, 'o-', color=C_RANDOM, label='Random selection',
            markersize=6, zorder=3)
    ax.plot(k_bm25, f1_bm25, 's', color=C_BM25, label='BM25 selection',
            markersize=8, zorder=4, markeredgecolor='white', markeredgewidth=0.8)

    # Annotate BM25 point
    ax.annotate(f'{f1_bm25[0]:.2f}%', xy=(k_bm25[0], f1_bm25[0]),
                xytext=(k_bm25[0] - 0.7, f1_bm25[0] + 0.8),
                fontsize=8, color=C_BM25, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=C_BM25, lw=0.8))

    ax.set_xlabel('Number of in-context examples ($k$)')
    ax.set_ylabel('Record F1 (%)')
    ax.set_xticks([0, 1, 2, 3])
    ax.set_ylim(10, 20)
    ax.legend(loc='upper left', framealpha=0.9)
    ax.set_title('ICL sensitivity to $k$ (Gemma 2B, dev set)')

    fig.tight_layout()
    path = os.path.join(MEDIA_DIR, 'icl_sensitivity_k.pdf')
    fig.savefig(path)
    print(f'Saved: {path}')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════
# Plot 2: Training curves (loss + F1) for best FT models
# ════════════════════════════════════════════════════════════════
def plot_training_curves():
    fig, axes = plt.subplots(1, 2, figsize=(5.5, 3.4), sharey=False)

    # Colors for additional metrics
    C_VAL_LOSS = '#e6550d'   # orange for val loss
    C_SQL_EM   = '#756bb1'   # purple for SQL EM

    # --- T5-small fine-tuned ---
    ax1 = axes[0]
    epochs_loss = [e for e, _, _ in ft_small_train_loss]
    losses = [l for _, l, _ in ft_small_train_loss]
    eval_eps = [e for e, *_ in ft_small_eval_metrics]
    eval_f1 = [f * 100 for _, f, *_ in ft_small_eval_metrics]
    # T5-small has: (epoch, record_f1, dev_loss, record_em, sql_em, error_rate)
    eval_val_loss = [dl for _, _, dl, *_ in ft_small_eval_metrics]

    ax1.plot(epochs_loss, losses, '-', color=C_LOSS, alpha=0.8, label='Train loss')
    ax1.plot(eval_eps, eval_val_loss, '--', color=C_VAL_LOSS, alpha=0.8, linewidth=1.0,
             marker='.', markersize=2, label='Val loss')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss', color=C_LOSS)
    ax1.tick_params(axis='y', labelcolor=C_LOSS)
    ax1.set_ylim(0.5, 4.2)

    ax1r = ax1.twinx()
    # Record F1 (subset evals, all except last)
    ax1r.plot(eval_eps[:-1], eval_f1[:-1], 'o-', color=C_FT_SMALL, markersize=3,
              label='Record F1 (subset)')
    # Record F1 (full dev eval, last point)
    ax1r.plot(eval_eps[-1], eval_f1[-1], 'D', color=C_FT_SMALL, markersize=5,
              markeredgecolor='black', markeredgewidth=0.5, label='Record F1 (full dev)')
    ax1r.set_ylabel('Record F1 (%)', color=C_FT_SMALL)
    ax1r.tick_params(axis='y', labelcolor=C_FT_SMALL)
    ax1r.set_ylim(30, 90)

    ax1.set_title('T5-small fine-tuned', fontsize=10)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1r.get_legend_handles_labels()
    ax1r.legend(lines1 + lines2, labels1 + labels2, loc='center right', fontsize=5.5,
                framealpha=0.9)

    # --- T5-base fine-tuned ---
    ax2 = axes[1]
    epochs_loss_b = [e for e, _ in ft_base_train_loss]
    losses_b = [l for _, l in ft_base_train_loss]
    eval_eps_b = [e for e, *_ in ft_base_eval_metrics]
    eval_f1_b = [f * 100 for _, f, *_ in ft_base_eval_metrics]
    # T5-base now has: (epoch, record_f1, dev_loss, record_em, sql_em, error_rate)
    eval_val_loss_b = [dl for _, _, dl, *_ in ft_base_eval_metrics]
    eval_sql_em_b = [se * 100 for _, _, _, _, se, _ in ft_base_eval_metrics]

    ax2.plot(epochs_loss_b, losses_b, '-', color=C_LOSS, alpha=0.8, label='Train loss')
    ax2.plot(eval_eps_b, eval_val_loss_b, '--', color=C_VAL_LOSS, alpha=0.8, linewidth=1.0,
             marker='.', markersize=2, label='Val loss')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Loss', color=C_LOSS)
    ax2.tick_params(axis='y', labelcolor=C_LOSS)
    ax2.set_ylim(1.0, 5.6)

    ax2r = ax2.twinx()
    # Record F1
    ax2r.plot(eval_eps_b[:-1], eval_f1_b[:-1], 'o-', color=C_FT_BASE, markersize=3,
              label='Record F1 (subset)')
    ax2r.plot(eval_eps_b[-1], eval_f1_b[-1], 'D', color=C_FT_BASE, markersize=5,
              markeredgecolor='black', markeredgewidth=0.5, label='Record F1 (full dev)')
    # SQL EM
    ax2r.plot(eval_eps_b[:-1], eval_sql_em_b[:-1], '^-', color=C_SQL_EM, markersize=2.5,
              linewidth=0.8, label='SQL EM (subset)')
    ax2r.plot(eval_eps_b[-1], eval_sql_em_b[-1], 'D', color=C_SQL_EM, markersize=4,
              markeredgecolor='black', markeredgewidth=0.5, label='SQL EM (full dev)')
    ax2r.set_ylabel('Metric (%)', color=C_FT_BASE)
    ax2r.tick_params(axis='y', labelcolor=C_FT_BASE)
    ax2r.set_ylim(-2, 95)

    ax2.set_title('T5-base fine-tuned', fontsize=10)
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2r.get_legend_handles_labels()
    ax2r.legend(lines1 + lines2, labels1 + labels2, loc='center right', fontsize=5.5,
                framealpha=0.9)

    fig.tight_layout()
    path = os.path.join(MEDIA_DIR, 'training_curves.pdf')
    fig.savefig(path)
    print(f'Saved: {path}')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════
# Plot 3: Dev F1 comparison bar chart
# ════════════════════════════════════════════════════════════════
def plot_dev_f1_comparison():
    fig, ax = plt.subplots(figsize=(5.5, 3.5))

    # Data from report tables — (label, F1, color_group)
    data = [
        # T5-small fine-tune variants
        ('Restricted v1',          45.49, 'ft'),
        ('Restricted v2',          66.32, 'ft'),
        ('Restricted v3 (best)',   79.60, 'ft_best'),
        ('+ freeze encoder',      75.45, 'ft'),
        ('+ high dropout',        69.89, 'ft'),
        # LoRA
        ('LoRA v1',               33.46, 'lora'),
        ('LoRA v2',               51.63, 'lora'),
        ('LoRA v3',               47.58, 'lora'),
        ('LoRA + freeze',         35.16, 'lora'),
        ('LoRA + warmstart',      73.38, 'lora'),
        # MLP
        ('MLP v1',                 8.67, 'mlp'),
        ('MLP v2',                 8.67, 'mlp'),
        # From scratch
        ('From scratch',          66.12, 'scr'),
    ]

    labels = [d[0] for d in data]
    f1s = [d[1] for d in data]
    color_map = {
        'ft':      '#6baed6',
        'ft_best': '#2166ac',
        'lora':    '#fc9272',
        'mlp':     '#a1d99b',
        'scr':     '#4daf4a',
    }
    colors = [color_map[d[2]] for d in data]

    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, f1s, color=colors, edgecolor='white', linewidth=0.5, height=0.7)

    # Add value labels
    for bar, f1 in zip(bars, f1s):
        ax.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height() / 2,
                f'{f1:.1f}', va='center', fontsize=7)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlabel('Record F1 (%)')
    ax.set_xlim(0, 95)
    ax.set_title('T5-small dev F1 across all variants')

    # Legend patches — place upper right so it doesn't cover bars
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#6baed6', label='Full fine-tune'),
        Patch(facecolor='#fc9272', label='LoRA'),
        Patch(facecolor='#a1d99b', label='MLP head'),
        Patch(facecolor='#4daf4a', label='From scratch'),
    ]
    ax.legend(handles=legend_elements, loc='upper center', fontsize=7, framealpha=0.9,
              bbox_to_anchor=(0.5, -0.15), ncol=4)

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.18)
    path = os.path.join(MEDIA_DIR, 'dev_f1_comparison.pdf')
    fig.savefig(path)
    print(f'Saved: {path}')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════
# Plot 4: Fine-tuned vs. from-scratch learning dynamics
# ════════════════════════════════════════════════════════════════
def plot_ft_vs_scratch():
    fig, ax = plt.subplots(figsize=(4.5, 3.0))

    # Fine-tuned: full trajectory (subset eval, epochs 3-75)
    ft_eps = [e for e, *_ in ft_small_eval_metrics[:-1]]  # exclude full-dev point
    ft_f1 = [f * 100 for _, f, *_ in ft_small_eval_metrics[:-1]]

    # From-scratch: combine milestones + late trajectory
    # Use milestones for the early story, late_f1 for detailed late trajectory
    scr_eps_all = [e for e, _ in scr_small_milestones]
    scr_f1_all = [f * 100 for _, f in scr_small_milestones]
    # Add late trajectory points not already in milestones
    milestone_epochs = set(scr_eps_all)
    for e, f in scr_small_late_f1:
        if e not in milestone_epochs:
            scr_eps_all.append(e)
            scr_f1_all.append(f * 100)
    # Sort by epoch
    sorted_scr = sorted(zip(scr_eps_all, scr_f1_all))
    scr_eps_all = [e for e, _ in sorted_scr]
    scr_f1_all = [f for _, f in sorted_scr]

    ax.plot(ft_eps, ft_f1, 'o-', color=C_FT_SMALL, markersize=3.5,
            label='T5-small fine-tuned (pretrained init)')
    ax.plot(scr_eps_all, scr_f1_all, 's-', color=C_SCRATCH, markersize=3.5,
            label='T5-small from scratch (random init)')

    # Mark best points
    ft_best_idx = np.argmax(ft_f1)
    scr_best_idx = np.argmax(scr_f1_all)
    ax.plot(ft_eps[ft_best_idx], ft_f1[ft_best_idx], '*', color=C_FT_SMALL,
            markersize=12, markeredgecolor='black', markeredgewidth=0.5, zorder=5)
    ax.plot(scr_eps_all[scr_best_idx], scr_f1_all[scr_best_idx], '*', color=C_SCRATCH,
            markersize=12, markeredgecolor='black', markeredgewidth=0.5, zorder=5)

    # Annotate best points
    ax.annotate(f'Best: {ft_f1[ft_best_idx]:.1f}%\n(ep {ft_eps[ft_best_idx]})',
                xy=(ft_eps[ft_best_idx], ft_f1[ft_best_idx]),
                xytext=(ft_eps[ft_best_idx] - 20, ft_f1[ft_best_idx] - 8),
                fontsize=7, color=C_FT_SMALL,
                arrowprops=dict(arrowstyle='->', color=C_FT_SMALL, lw=0.7))
    ax.annotate(f'Best: {scr_f1_all[scr_best_idx]:.1f}%\n(ep {scr_eps_all[scr_best_idx]})',
                xy=(scr_eps_all[scr_best_idx], scr_f1_all[scr_best_idx]),
                xytext=(scr_eps_all[scr_best_idx] + 5, scr_f1_all[scr_best_idx] + 5),
                fontsize=7, color=C_SCRATCH,
                arrowprops=dict(arrowstyle='->', color=C_SCRATCH, lw=0.7))

    # Visual separator: show gap between data regions
    ax.axvspan(76, 94, alpha=0.06, color='gray')
    ax.text(85, 42, 'no data', fontsize=6, color='gray', ha='center', va='center',
            fontstyle='italic')

    ax.set_xlabel('Epoch')
    ax.set_ylabel('Record F1 (%)')
    ax.set_title('Pretrained vs. random initialization')
    ax.set_ylim(38, 85)
    ax.set_xlim(-2, 205)
    ax.legend(loc='lower right', fontsize=7, framealpha=0.9)

    fig.tight_layout()
    path = os.path.join(MEDIA_DIR, 'ft_vs_scratch_dynamics.pdf')
    fig.savefig(path)
    print(f'Saved: {path}')
    plt.close(fig)


# ════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    os.makedirs(MEDIA_DIR, exist_ok=True)
    plot_icl_sensitivity()
    plot_training_curves()
    plot_dev_f1_comparison()
    plot_ft_vs_scratch()
    print('\nAll plots generated successfully.')
