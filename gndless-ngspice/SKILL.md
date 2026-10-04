---
name: gndless-ngspice
description: Use when running standalone ngspice (not KiCad's embedded simulator) from the CLI, including batch decks, .control blocks, .op/.tran/.ac analysis, parameter sweeps, .meas measurements, Fourier/THD checks, rawfile and 32-bit float WAV export, and diagnosing failed or suspicious runs.
---

# Gndless ngspice

単体ngspice（CLI）を AI エージェントが操作するための前提と注意点。アナログ回路のバッチ解析、raw/WAV/表の出力、結果がおかしいときの切り分け方。

## Prerequisites

- **単体 CLI 専用**。KiCad 内蔵シミュレータは共有ライブラリ + GUI の別物で、`-b` / `-r` / `-o` や `.control` のファイル出力系はそのままでは使えない。
- このスキルは ngspice 47 を前提とする。オプション名や既定値はバージョン差があるため、最初に `ngspice --version` を確認する。
- インストール（macOS）は `brew install ngspice ffmpeg`。WAV 変換に ffmpeg を使う。
- デッキは手書きせず、ケースごとにスクリプトで生成して `.param` を埋める。ngspice に `.step` は無い。
- 既定温度は TEMP=27°C。再現性が要る比較では `.temp` または `.options temp=` を明示する。
- `.include` の相対パスはデッキのあるディレクトリ基準。生成スクリプトと出力先を揃える。

## Commands

| Purpose | Command |
|---|---|
| Batch + log | `ngspice -b -o log.txt deck.cir` |
| Binary raw output | `ngspice -b -r out.raw deck.cir` |
| Interactive (debug) | `ngspice deck.cir` |

`-b` の stdout はノイズが多い。`-o log.txt` を付けて `.meas` や `fourier` の結果をログから読む。解析前にログの `Error` / `Warning` を確認する。

## Basic flow

1. デッキを生成して `ngspice -b -o log.txt deck.cir` を実行する。
2. 動作点 `.op` → 過渡 `.tran` → 周波数特性 `.ac` の順で確認する。
3. 出力は `.control` の `wrdata`（gnuplot 向き）または `write`（raw）を使う。
4. 数値は理論値と突き合わせてから結論を出す。FFT やスイープ集計は Python 側で行う。

## Deck gotchas

- **1 行目はタイトルとして消費される**。`.param` や素子を書くと無効になる。
- **接尾辞**: `M` はミリ、`Meg` はメガ。`2M` は 2 mΩ。大抵抗は必ず `Meg` を使う（`2e+06` の誤解析事例あり）。
- SIN 源は `SIN(VO VA FREQ TD THETA PHASE)`。B-source で `.param` を参照するときは `{PARAM}` と書き、`{...}` 内では三項演算子 `?:` が使える。
- **直列ソース抵抗**: `Bsrc src 0 V=...` + `Rsrc src tri 1k` の形にする。`Bsrc tri 0` のまま抵抗を浮いたノード（`tri_s`）へ繋ぐと抵抗が効かない。
- **`.meas` は `FROM=` / `TO=` と等号必須**。`FROM 2m TO 4m` は構文エラーになる（LTspice と非互換）。
- `.control` 内では `wrdata` を `run` 直後に置く。`op` など別解析の後だとカレントプロットが変わり time 列が消える。
- 等間隔サンプルが欲しいときは `linearize` を使う。**出力サンプルレートは `.tran` の tstep で決まる**ので、`{1/fs}` と書けば正確になる（例: `.tran {1/96000} 5m`）。
- 収束不良には `.options reltol=... gmin=...`、`method=gear`、`.ic`、怪しいノードへの 1 GΩ 追加を試す。

## AC analysis

```spice
.ac dec 100 10 1Meg          ; decade 100 点、10 Hz〜1 MHz

.control
run
set wr_singlescale
set numdgt=15
wrdata ac.dat vdb(out) vp(out)
.endc
```

- 複素ベクトルをそのまま `wrdata` すると実部・虚部が並ぶ。dB と位相は `vdb()` / `vp()` を明示する。
- `plot vdb(out)` は対話時のみ。バッチでは `wrdata` か `write` を使う。

## Analysis gotchas

- 高調波 DFT は整数周期の窓で計算する。離散和での基本波係数は `Σv·sin / Σsin²` であり、連続積分の `2/T` をそのまま使うと 2 倍になる。
- **`fourier` / `.four` は最後の 1 周期だけを使う**。`tstop` を信号周期の整数倍にしないと THD を信用できない。`fourier 1k v(out)` で THD が直接出る。
- スイープは 1 ケースずつ実行し、各ケースのログに収束エラーが無いか確認する。

## Output precision

| Path | Precision | Use |
|---|---|---|
| Internal | double (binary64, 53-bit significand) | Always |
| Binary raw (`-r` / `write`) | 8 byte per value (double) | Exact numeric comparison |
| `wrdata` text | `set numdgt=N`, default 9 digits | gnuplot. **Set `numdgt=15`** |
| WAV | 32-bit float (24-bit significand) | Audio output |

- raw を ASCII にするときは `write` の前に `set filetype=ascii` を置く。
- **LTspice の .raw / .wave とは非互換**。
- `wrdata` は `set wr_vecnames` でヘッダ行、`set wr_singlescale` で複数ベクトルでも 1 スケール + 複数列になる（付けないとベクトルごとにスケール列が繰り返される）。

## WAV export

ngspice は WAV を直接書けない。**バイナリ raw（float64）を書き、ffmpeg で 32-bit float WAV に変換**する。

```spice
.control
run
linearize v(out)
write out.raw v(out)            ; time + 指定ベクトル
.endc
```

```sh
# raw は "Binary:\n" の後ろが float64 interleaved（c0=time, c1=信号）
OFF=$(LC_ALL=C grep -abo 'Binary:' out.raw | cut -d: -f1)
tail -c +$((OFF+9)) out.raw | ffmpeg -y -f f64le -ar 96000 -ac 2 -i - \
  -af "pan=mono|c0=c1,volume=1.0" -c:a pcm_f32le out.wav
```

- `linearize` をしないとサンプル間隔が不均一になり `-ar` が成立しない。
- `write out.raw` にベクトルを列挙しないとプロット内の全ベクトルを書く。列挙しても time が先頭に入るので、ffmpeg は常に 2ch として読み `pan` で信号列（c1）だけ取る。
- `-ar` は tstep の逆数と一致させる。既定は 96 kHz で `.tran {1/96000}` を使う。`10.4167u` のような丸めでも誤差は 0.0003% 程度。
- **ngspice 側でスケールしない**。音量は `volume`（線形倍率）で調整する。32-bit float 出力は ±1 超えでもクリップしない。
- **ffmpeg は既定で上書きしない**ので `-y` を付ける。

## Anti-patterns

- WAV 変換で time 列（c0）を信号として渡す。
- `write` の出力ベクトルを増やしてチャンネル数を変える（`-ac 2` 前提が壊れる）。
- `fourier` / `.four` を非整数周期の `tstop` で回して THD を信用する。
- `.meas` を LTspice 流の `FROM 2m TO 4m` で書く。
