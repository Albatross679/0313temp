# Neural Network Computation Graph Rules

Rules for generating neural network architecture diagrams in draw.io format. Apply these conventions whenever the user requests an NN architecture, computation graph, or model diagram via the drawio skill.

## Math/LaTeX Setup

Enable MathJax by setting `math="1"` on the root `<mxGraphModel>` element:

```xml
<mxGraphModel math="1" dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" background="#ffffff">
```

- Inline LaTeX: `\(` ... `\)` delimiters
- Display LaTeX: `$$` ... `$$` delimiters
- HTML labels (`html=1`) and math coexist in the same cell value
- Escape XML entities in LaTeX: `&lt;` for `<`, `&gt;` for `>`, `&amp;` for `&`
- **VS Code caveat:** The VS Code draw.io extension has a known math rendering bug — formulas may appear as raw LaTeX in preview. Desktop app and CLI export render correctly.

## Color Palette

Use consistently across all NN diagrams. Stroke colors are the 800-shade Material Design variant.

| Component | Fill | Stroke | Font | Hex Name |
|-----------|------|--------|------|----------|
| Input/Output | `#2196F3` | `#1565C0` | `#ffffff` | Blue |
| Embedding | `#4CAF50` | `#2E7D32` | `#ffffff` | Green |
| Self-Attention | `#E91E63` | `#AD1457` | `#ffffff` | Pink |
| Cross-Attention | `#EC407A` | `#C2185B` | `#ffffff` | Light Pink |
| Layer Normalization | `#00BCD4` | `#00838F` | `#ffffff` | Cyan |
| Feed-Forward Network | `#FF9800` | `#EF6C00` | `#ffffff` | Orange |
| Linear Projection | `#9C27B0` | `#6A1B9A` | `#ffffff` | Purple |
| Residual/Add | `#607D8B` | `#37474F` | `#ffffff` | Blue-Grey |
| Softmax | `#009688` | `#00695C` | `#ffffff` | Teal |
| Loss Function | `#F44336` | `#C62828` | `#ffffff` | Red |
| Dropout/Regularization | `#795548` | `#4E342E` | `#ffffff` | Brown |
| Positional Encoding | `#CDDC39` | `#9E9D24` | `#333333` | Lime |
| Activation Function | `#FF5722` | `#D84315` | `#ffffff` | Deep Orange |
| Concatenation | `#78909C` | `#455A64` | `#ffffff` | Grey |

## Component Shapes

### Standard node style (base template)

```
rounded=1;whiteSpace=wrap;html=1;fillColor={FILL};strokeColor={STROKE};fontColor=#ffffff;fontSize=12;arcSize=20;
```

### Node with formula and tensor shape

```xml
<mxCell id="mha1" value="&lt;b&gt;Multi-Head Attention&lt;/b&gt;&lt;br&gt;&lt;font style=&quot;font-size:10px&quot;&gt;$$\text{Attn}(Q,K,V)$$&lt;/font&gt;&lt;br&gt;&lt;font style=&quot;font-size:9px;opacity:0.7&quot;&gt;(B, T, d) &amp;rarr; (B, T, d)&lt;/font&gt;"
  style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E91E63;strokeColor=#AD1457;fontColor=#ffffff;fontSize=12;arcSize=20;"
  vertex="1" parent="1">
  <mxGeometry x="200" y="300" width="200" height="80" as="geometry"/>
</mxCell>
```

### Compact node (LayerNorm, Dropout)

Height 35-40px, no formula. Good for operations that don't need detail.

```xml
<mxCell id="ln1" value="&lt;b&gt;LayerNorm&lt;/b&gt;"
  style="rounded=1;whiteSpace=wrap;html=1;fillColor=#00BCD4;strokeColor=#00838F;fontColor=#ffffff;fontSize=11;arcSize=20;"
  vertex="1" parent="1">
  <mxGeometry x="200" y="400" width="200" height="35" as="geometry"/>
</mxCell>
```

### Residual Add node (circular)

Small ellipse with `+` label. 40x40px.

```xml
<mxCell id="add1" value="&lt;b&gt;+&lt;/b&gt;"
  style="ellipse;whiteSpace=wrap;html=1;fillColor=#607D8B;strokeColor=#37474F;fontColor=#ffffff;fontSize=18;fontStyle=1;"
  vertex="1" parent="1">
  <mxGeometry x="270" y="440" width="40" height="40" as="geometry"/>
</mxCell>
```

### Concatenation node (circular)

```xml
<mxCell id="cat1" value="&lt;b&gt;⊕&lt;/b&gt;"
  style="ellipse;whiteSpace=wrap;html=1;fillColor=#78909C;strokeColor=#455A64;fontColor=#ffffff;fontSize=18;fontStyle=1;"
  vertex="1" parent="1">
  <mxGeometry x="270" y="440" width="40" height="40" as="geometry"/>
</mxCell>
```

## Container Patterns (Layer Grouping)

Use swimlane containers to group components into layers. Children use `parent="containerId"` with **relative** coordinates.

### Transformer layer container

```xml
<mxCell id="enc_layer1" value="Encoder Layer 1"
  style="swimlane;startSize=30;fillColor=#FAFAFA;strokeColor=#E0E0E0;fontColor=#333333;fontSize=13;fontStyle=1;rounded=1;arcSize=8;swimlaneLine=0;shadow=0;"
  vertex="1" parent="1">
  <mxGeometry x="100" y="150" width="320" height="520" as="geometry"/>
</mxCell>
```

### Rules for containers

- Always set `parent="containerId"` on child cells — never place children at root with overlapping coordinates
- Use `swimlaneLine=0;` to remove the header underline for cleaner look
- Container width: 280-320px for single-column layouts
- Container padding: 50-60px from edges for child nodes
- Limit nesting to 2 levels: architecture → layer. Put sub-component detail in node labels.

## Edge Conventions

### Data flow (forward pass)

Standard top-to-bottom connections. Center-to-center routing.

```xml
<mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#666666;strokeWidth=2;endArrow=block;endFill=1;"
  edge="1" parent="1" source="mha1" target="ln1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### Residual/skip connections

Route on RIGHT side of nodes. Dashed, curved, using residual color.

```xml
<mxCell id="res1" value=""
  style="edgeStyle=orthogonalEdgeStyle;curved=1;rounded=1;strokeColor=#607D8B;strokeWidth=2;dashed=1;dashPattern=8 4;exitX=1;exitY=0.5;entryX=1;entryY=0.5;endArrow=block;endFill=1;"
  edge="1" parent="1" source="input_node" target="add_node">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="290" y="90"/>
      <mxPoint x="290" y="170"/>
    </Array>
  </mxGeometry>
</mxCell>
```

### Edge style reference

| Connection Type | curved | dashed | strokeColor | strokeWidth | Use For |
|----------------|--------|--------|-------------|-------------|---------|
| Data flow | 0 | 0 | `#666666` | 2 | Main forward pass |
| Residual/skip | 1 | 1 | `#607D8B` | 2 | Bypass connections |
| Attention paths | 0 | 0 | `#E91E63` | 1.5 | Q/K/V splits |
| Gradient flow | 1 | 1 | `#F44336` | 1.5 | Backprop visualization |
| Optional/conditional | 0 | 1 | `#999999` | 1 | Dropout, optional paths |

### Critical edge rules

- **Every edge must contain** `<mxGeometry relative="1" as="geometry"/>` — self-closing edge cells are invalid
- All edges use `edgeStyle=orthogonalEdgeStyle;rounded=1;` unless explicitly diagonal
- Add `endArrow=block;endFill=1;` for solid arrowheads
- Spread residual waypoints 30px right of the rightmost node edge

## Layout Guidelines

- Node width: 200px standard, 280px for formula-heavy nodes
- Node height: 35-40px compact, 60-80px standard, 80-100px with formula
- Vertical gap between nodes: 20-30px within a layer
- Horizontal gap between parallel paths: 80-100px
- Container padding: 50-60px from each side
- Align all coordinates to grid (multiples of 10)

## Tensor Shape Annotations

Include tensor shapes as a secondary line in the node label:

```
&lt;font style=&quot;font-size:9px;opacity:0.7&quot;&gt;(B, T, d) &amp;rarr; (B, T, d)&lt;/font&gt;
```

Convention: `(B, T, d)` format where B=batch, T=sequence length, d=model dimension. Use `&amp;rarr;` for input→output.

## Architecture-Specific Patterns

### Pre-Norm Transformer (GPT-style)

LayerNorm → Attention → Add → LayerNorm → FFN → Add

### Post-Norm Transformer (Original)

Attention → Add → LayerNorm → FFN → Add → LayerNorm

### Encoder-Decoder

- Encoder layers stacked vertically on the left
- Decoder layers stacked vertically on the right
- Cross-attention edges go `horizontal_right` from encoder to decoder
- Use `exitX=1;exitY=0.5` on encoder output, `entryX=0;entryY=0.5` on cross-attention

### Multi-Head Detail (Expanded View)

When showing attention head detail, place Q/K/V projections as three parallel nodes feeding into a single attention node. Use a group container (not swimlane) for the head:

```xml
<mxCell id="head_grp" value="" style="group;" vertex="1" parent="attn_container">
  <mxGeometry x="10" y="50" width="280" height="120" as="geometry"/>
</mxCell>
```
