---
name: pseudo-code-algorithm
description: >
  Generate publication-quality pseudo-code for algorithms in LaTeX (algpseudocode/algorithm2e) or markdown.
  Covers ML/deep learning (training loops, optimizers, backprop), reinforcement learning (Q-learning, PPO,
  actor-critic, REINFORCE), and evolutionary algorithms (GA, CMA-ES, NEAT, GP).
  Use when: (1) Writing pseudo-code for a paper, report, or assignment,
  (2) Converting Python/PyTorch code to pseudo-code,
  (3) Presenting an algorithm in LaTeX algorithm environment,
  (4) Creating pseudo-code for ML training, RL, or evolutionary methods,
  (5) User asks to "write pseudo-code", "algorithmize", or "present as algorithm".
---

# Pseudo-Code Algorithm Generator

Generate pseudo-code following established conventions from seminal ML/RL/EA papers.
For full examples and domain-specific patterns, read [references/algorithms-research.md](references/algorithms-research.md).

## Workflow

### 1. Detect Domain

Classify the algorithm into one of:

| Domain | Structural Pattern | Style |
|--------|-------------------|-------|
| **Neural Network / DL** | forward-backward-update loop | CLRS/Goodfellow style |
| **Reinforcement Learning** | interact-compute-update loop | Sutton-Barto or CLRS style |
| **Evolutionary** | initialize-evaluate-select-reproduce loop | Procedural with set notation |
| **General / Other** | varies | CLRS style (default) |

### 2. Select Output Format

- **LaTeX** (default for papers/reports): Use `algpseudocode` + `algorithm` package unless user specifies `algorithm2e`
- **Markdown**: Plain-text pseudo-code blocks with consistent formatting

### 3. Apply Formatting Rules

These 10 rules apply to ALL pseudo-code regardless of domain:

1. **One statement per line**
2. **Indent to show hierarchy** (not braces)
3. **Mathematical notation over code syntax** (`nabla`, `sum`, `argmax` -- not `for x in range(n)`)
4. **Left-arrow for assignment** (`theta <- ...`, not `=`). Equals is for equality testing only
5. **Capitalize keywords consistently** (Title-case: `While`, `If`, `Return`)
6. **Number and caption algorithms** ("Algorithm 1: Name")
7. **List hyperparameters in Input/Require section** -- never buried in loop body
8. **Comments explain "why", not "what"**
9. **Consistent notation**: bold for vectors (`theta`), calligraphic for sets/losses (`L`, `D`), greek for scalars (`alpha`)
10. **Self-contained**: readable from the algorithm box alone

### 4. Follow Domain-Specific Structure

**Neural Networks** -- Four canonical steps in the inner loop:
```
forward pass -> loss computation -> backward pass (backprop) -> parameter update
```
Early stopping sits between epochs. Validation is NOT inside the batch loop.

**Reinforcement Learning** -- Three-phase skeleton:
```
1. Initialize (parameters, value estimates, environment)
2. Loop (episodes or iterations):
   a. Interact with environment (collect experience)
   b. Compute targets (returns, advantages, TD errors)
   c. Update parameters (policy, value function, or both)
3. Return (policy, value function)
```
Use uppercase single letters for random variables (S, A, R). Advantage uses hat notation (A_hat).

**Evolutionary Algorithms** -- Population-level loop:
```
1. Initialize population
2. while not converged:
   a. Evaluate fitness
   b. Select parents
   c. Apply variation operators (crossover, mutation)
   d. Select survivors
3. Return best
```
Use (mu, lambda) notation. Set notation for population operations (union, empty set).

### 5. Avoid Anti-Patterns

- No programming-language syntax (`loss.backward()`, `for x in range(n)`)
- No implementation details (data loading, logging, checkpointing, device management)
- No ambiguous `=` for assignment
- No missing initialization -- always show initial values before the loop
- No unlabeled algorithms -- always "Algorithm N: Name"
- No monolithic blocks >20 lines -- decompose into sub-procedures with `\Call{}`

## LaTeX Quick Reference

### algpseudocode (recommended)

```latex
\usepackage{algorithm}
\usepackage{algpseudocode}

\begin{algorithm}[t]
\caption{Algorithm Name}\label{alg:name}
\begin{algorithmic}[1]
\Require Input description
\Ensure Output description
\State $\boldsymbol{\theta} \gets \boldsymbol{\theta}_0$ \Comment{Initialize}
\While{not converged}
    \State $\mathbf{g} \gets \nabla_{\boldsymbol{\theta}} \mathcal{L}$
    \State $\boldsymbol{\theta} \gets \boldsymbol{\theta} - \alpha \mathbf{g}$
\EndWhile
\State \textbf{return} $\boldsymbol{\theta}$
\end{algorithmic}
\end{algorithm}
```

Key commands: `\Require`, `\Ensure`, `\State`, `\If{} ... \EndIf`, `\While{} ... \EndWhile`,
`\For{} ... \EndFor`, `\ForAll{} ... \EndFor`, `\Procedure{Name}{params} ... \EndProcedure`,
`\Function{Name}{params} ... \EndFunction`, `\Call{Name}{args}`, `\Comment{text}`.

### algorithm2e (alternative)

```latex
\usepackage[ruled,lined,linesnumbered]{algorithm2e}

\begin{algorithm}[H]
\caption{Algorithm Name}\label{alg:name}
\KwIn{Input description}
\KwOut{Output description}
\While{not converged}{
    $\mathbf{g} \gets \nabla_{\boldsymbol{\theta}} \mathcal{L}$\;
    $\boldsymbol{\theta} \gets \boldsymbol{\theta} - \alpha \mathbf{g}$\;
}
\Return{$\boldsymbol{\theta}$}
\end{algorithm}
```

Key commands: `\KwIn{}`, `\KwOut{}`, `\KwData{}`, `\KwResult{}`, lines end with `\;`,
`\eIf{cond}{true}{false}`, `\If{cond}{body}`, `\While{cond}{body}`, `\For{cond}{body}`,
`\tcc{multi-line comment}`, `\tcp{single-line comment}`.

**Critical:** These two package families are mutually exclusive. Never load both.

## Detailed Reference

For complete examples of every algorithm type (Adam, PPO, GA, CMA-ES, NEAT, Q-learning, etc.)
with full LaTeX code, read [references/algorithms-research.md](references/algorithms-research.md).

Key sections to grep for:
- `## Neural Network Algorithms` -- training loops, Adam, backprop, architectures
- `## Reinforcement Learning Algorithms` -- Q-learning, SARSA, REINFORCE, PPO, A2C
- `## Evolutionary Algorithms` -- GA, ES, CMA-ES, OpenAI ES, NEAT, GP
- `## Code Examples` -- complete copy-paste LaTeX for Adam, PPO, GA, Q-learning
- `## Recommended References` -- seminal papers and textbooks
