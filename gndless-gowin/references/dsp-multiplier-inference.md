# Gowin DSP乗算の推論 (GW5A-25A)

2026-11 に GW5A-25A (GW5A-LV25MG121NC1/I0) で `GowinSynthesis` の netlist を確認した実測。合成のみで PnR は未実施。Gowin EDA のバージョンによって挙動が変わる可能性がある。

## 結論

`MULTALU27X18` (1 DSP) と `MULT27X36` (2 DSP) の選択は、積の宣言幅では決まらない。**符号拡張後のオペランドが DSP の入力幅に収まるか**で決まる。

- `MULTALU27X18` の入力は signed: A=27bit、B=18bit
- unsigned は正の signed として扱うため、A/B それぞれにゼロ拡張1bitが必要
- 27×18に収まる条件:
  - unsigned: `A <= 26` かつ `B <= 17`
  - signed: `A <= 27` かつ `B <= 18`
- これを超えると `MULT27X36` になる
- signed 同士なら42〜45bit積でも 27×18 になる
- `syn_dspstyle` は DSP / logic の選択のみ。27×18 / 27×36 を選ぶ属性は SUG550 に見当たらない

## 実測表

| 乗算 | 宣言積 | 符号拡張後 | 推論 |
| --- | ---: | --- | --- |
| 24u × 12u | 36 | 25 × 13 | MULTALU27X18 |
| 25u × 12u | 37 | 26 × 13 | MULTALU27X18 |
| 25s × 12s | 37 | 25 × 12 | MULTALU27X18 |
| 25u × 13u | 38 | 26 × 14 | MULTALU27X18 |
| 24u × 14u | 38 | 25 × 15 | MULTALU27X18 |
| 24u × 17u | 41 | 25 × 18 | MULTALU27X18 |
| 24u × 18u | 42 | 25 × 19 | MULT27X36 |
| 24s × 18s | 42 | 24 × 18 | MULTALU27X18 |
| 25u × 18u | 43 | 26 × 19 | MULT27X36 |
| 25s × 18s | 43 | 25 × 18 | MULTALU27X18 |
| 27u × 14u | 41 | 28 × 15 | MULT27X36 |
| 27u × 18u | 45 | 28 × 19 | MULT27X36 |
| 27s × 18s | 45 | 27 × 18 | MULTALU27X18 |

## 設計時の指針

- 27×18 に収めたいときは、unsigned のオペランドを A≤26bit、B≤17bit に抑える
- 幅を削りたくないときは signed にする。値が非負でも、最上位bitが0なら signed として正しく扱える
- 積の宣言幅が37bit以上でも、符号拡張後のオペランドが収まれば 27×18 になる
- unsigned のまま A=27bit や B=18bit にすると 27×36 になりやすい

## 実験方法

- 一時ディレクトリに `dsp_width_test` プロジェクトを作成
- `create_project -pn "GW5A-LV25MG121NC1/I0" -device_version "A"`
- 各乗算を個別の出力レジスタへ接続し、`run all` で合成
- PnR は I/O 数超過で失敗するが、`impl/gwsynthesis/*.vg` は生成される
- `.vg` 内の `MULTALU27X18` / `MULT27X36` インスタンスを確認

## 注意

- この表は合成時の推論であり、配置配線後のFmaxやDSP配置は別途確認する
- signed のオペランドは値域がDSPの入力幅に収まることをRTLで保証する
- `syn_dspstyle=dsp` は「ロジックに落とさずDSPを使う」だけで、27×18 / 27×36 の選択には効かない
