---
name: gndless-ngspice
description: Use when simulating analog circuits with standalone ngspice (not KiCad's embedded simulator), including batch decks, control blocks, parameter/pot sweeps, THD and harmonic analysis, rawfile/WAV export, and diagnosing simulation results that look wrong.
---

# Gndless ngspice

単体 ngspice でアナログ回路（差動対、フィルタ、VCA など）を検証するときの
作業方針と、実際に踏んだ落とし穴。

## 使う場面

- ngspice で動作点・過渡・周波数特性・THD を確認する
- 部品値やポット位置をスイープして表・グラフ・WAV にする
- シミュレーション結果が理論値や直感と合わないとき

## 基本フロー

- デッキはスクリプトでケースごとに生成し、`.param` を埋めて
  `ngspice -b -o log deck.cir` で回す（ngspice に `.step` は無い）
- 出力は `.control` ブロックの `wrdata`（gnuplot 向き）または `write`（raw）
- 解析は Python 側で行い、理論値で DFT を検算してから結論を出す
- 動作点（`.op`）→ 過渡（`.tran`）の順で確認する

## デッキの落とし穴

- **1 行目はタイトルとして消費される**。`.param` を 1 行目に書くと無効
- **接尾辞**: `M` はミリ、`Meg` はメガ。`2M` は 2 mΩ。大抵抗は必ず `Meg`
  （`2e+06` のような指数表記が誤解析された事例もあり `Meg` が安全）
- B-source の式で `.param` を参照するときは `{PARAM}`。`{...}` 内は
  三項演算子 `?:` が使える
- **直列ソース抵抗**: `Bsrc src 0 V=...` + `Rsrc src tri 1k` の形にする。
  `Bsrc tri 0` のまま `Rsrc tri_s tri 1k` のように浮いたノードへ繋ぐと
  ソース抵抗が効かない（最適点がずれる典型ミス）
- `.control` 内では `wrdata` を `run` 直後に置く。`op` の後だとカレント
  プロットが変わり time 列が消える
- 等間隔サンプルが欲しいときは `linearize`。**WAV のサンプルレートは
  `.tran` の tstep で決まる**（例: 96 kHz → `10.4167u`、48 kHz → `20.8333u`）
- 収束不良: `.options reltol=... gmin=...`、`method=gear`、
  `.ic`、怪しいノードに 1 GΩ を追加

## 出力

- rawfile: `ngspice -b -r out.raw deck.cir`（バイナリ SPICE3 形式）、
  または control 内で `write out.raw v(x)`。ASCII は `set filetype=ascii`
- **LTspice の .raw / .wave とは非互換**。ngspice に WAV 出力は無いので
  `linearize` → `wrdata`/`write` → Python `wave` モジュールや sox で変換する
- `wrdata` は `set wr_vecnames` `set wr_singlescale` を付けると
  1 スケール + 複数列になり gnuplot で扱いやすい
- レベルを揃えるかは明示する。固定スケール（例: ±2.5 V → 0.9 FS）なら
  ファイル間の相対レベルが保たれる

## データ精度（どの段が律速か）

- ngspice の内部演算は **double**（IEEE754 binary64、仮数 53 bit）
- バイナリ rawfile（`-r` / `write`）は **1 値 8 バイトの double**
  （実測: `databytes / (nvars * npoints) = 8.0`）
- `wrdata` のテキストは `set numdgt=N` で桁数制御。既定は 9 桁程度
  （相対精度 ~30 bit 相当）なので **`set numdgt=15` を入れる**
- WAV のビット深度: 24-bit PCM は仮数 24 bit（相対 ~7.2 桁）。
  32-bit float も仮数 24 bit でフルスケール時は 24-bit PCM と同等。
  double 相当が欲しいなら 64-bit float WAV（`-e floating-point -b 64`）
- 音声用途は 24-bit で十分。数値解析の厳密比較は rawfile（double）を使う

## 解析の落とし穴

- 高調波 DFT は整数周期の窓で計算する。離散和での基本波係数は
  `Σv·sin / Σsin²`。連続積分の `2/T` をそのまま使うと 2 倍になる
- THD は「正弦波からのずれ」。三角波は素通しでも ≈12%（H3≈11.1%）出る
- 奇関数（対称差動対）は偶数次を出さない。非対称は DC バイアス、
  レベルはテール電流で作る
- コレクタ電源電圧を変えると **Early 効果で H3 打ち消し点（サイン点）が動く**。
  「サイン点」は tanh 圧縮と Early 効果の兼ね合いで決まる
- ソースインピーダンス、ベースの rπ、ポットの負荷を見落とすと最適点がずれる
- 結果が変なら、まずモデル・接尾辞・ソース抵抗を疑う

## 波形（WAV）レシピ

ngspice は WAV を直接書けない。**バイナリ raw（float64）を書き、
ffmpeg で 32-bit float WAV に変換**するのが最も単純。使用ツールは
ngspice と ffmpeg の 2 つだけ（変換は ffmpeg、Python/awk/sox 不要）。

```spice
.control
run
linearize v(outj)
write out.raw v(outj)           ; 指定ベクトルだけの raw（time + 信号）
.endc
```

```sh
# raw は "Binary:\n" の後ろが float64 interleaved（c0=time, c1=信号）
OFF=$(LC_ALL=C grep -abo 'Binary:' out.raw | cut -d: -f1)
tail -c +$((OFF+9)) out.raw | ffmpeg -y -f f64le -ar 96000 -ac 2 -i - \
  -af "pan=mono|c0=c1,volume=1.0" -c:a pcm_f32le out.wav
```

- `write out.raw v(x)` は time + 指定ベクトルだけの raw を書く（2ch）
- **ngspice 側でスケールしない**（電圧のまま出す）。音量は変換側の
  `volume`（線形倍率）で調整。float 出力は ±1 超えでもクリップしない
- **ffmpeg は既定で既存ファイルを上書きしない**ので `-y` を付ける
- サンプルレートは `linearize` の tstep（= `.tran` の tstep）で決まる
- 仮数は 24bit（`pcm_f32le`）。double のまま欲しいときは `pcm_f64le`
- 参考: sox の `dat`（テキスト）入力は ±1.0 でクリップするため使わない
