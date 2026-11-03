---
name: gndless-ngspice
description: Use when running standalone ngspice from the CLI, including batch decks, .control, .meas, Fourier/THD, raw/WAV export, and diagnosing bad runs.
---

# Gndless ngspice

単体 ngspice (CLI) のバッチ解析と、結果がおかしいときの切り分け。KiCad 内蔵シミュレータは共有ライブラリ + GUI の別物で、`-b` / `-r` / `-o` や `.control` のファイル出力系はそのまま使えない。

## 前提

- ngspice 47 を前提とする。オプション名や既定値はバージョン差があるため、最初に `ngspice --version` を確認する
- macOS の導入は `brew install ngspice ffmpeg`。WAV 変換に ffmpeg を使う
- デッキは手書きせず、ケースごとにスクリプトで生成して `.param` を埋める。ngspice に `.step` は無い
- 既定温度は TEMP=27°C。比較では `.temp` または `.options temp=` を明示する
- `.include` の相対パスはデッキのあるディレクトリ基準

## 実行

| 用途 | コマンド |
|---|---|
| バッチ + ログ | `ngspice -b -o log.txt deck.cir` |
| バイナリ raw | `ngspice -b -r out.raw deck.cir` |
| 対話デバッグ | `ngspice deck.cir` |

`-b` の stdout はノイズが多い。`-o log.txt` を付け、`.meas` や `fourier` の結果をログから読む。解析前に `Error` / `Warning` を確認する。

## デッキの注意

- 1行目はタイトルとして消費される。`.param` や素子を書くと無効になる
- `M` はミリ、`Meg` はメガ。`2M` は 2 mΩ。大抵抗は `Meg` か `2e+06` を使う
- SIN 源は `SIN(VO VA FREQ TD THETA PHASE)`。B-source で `.param` を参照するときは `{PARAM}` と書き、`{...}` 内では三項演算子 `?:` が使える
- 直列ソース抵抗は `Bsrc src 0 V=...` + `Rsrc src tri 1k` の形にする。`Bsrc tri 0` のまま浮いたノードへ繋ぐと抵抗が効かない
- `.meas` は `FROM=` / `TO=` と等号必須。`FROM 2m TO 4m` は構文エラーになる (LTspice と非互換)
- `.control` 内では `wrdata` を `run` 直後に置く。`op` など別解析の後だとカレントプロットが変わり time 列が消える
- 等間隔サンプルは `linearize` を使う。出力サンプルレートは `.tran` の tstep で決まるため、`{1/fs}` と書けば正確になる (例: `.tran {1/96000} 5m`)
- 収束不良には `.options reltol=... gmin=...`、`method=gear`、`.ic`、怪しいノードへの 1 GΩ 追加を試す

## AC 解析

```spice
.ac dec 100 10 1Meg

.control
run
set wr_singlescale
set numdgt=15
wrdata ac.dat vdb(out) vp(out)
.endc
```

複素ベクトルをそのまま `wrdata` すると実部・虚部が並ぶ。dB と位相は `vdb()` / `vp()` を明示する。`plot` は対話時のみで、バッチでは `wrdata` か `write` を使う。

## 解析結果の注意

- 高調波 DFT は整数周期の窓で計算する。離散和の基本波係数は `Σv·sin / Σsin²` であり、連続積分の `2/T` をそのまま使うと2倍になる
- `fourier` / `.four` は最後の1周期だけを使う。`tstop` を信号周期の整数倍にしないと THD を信用できない。`fourier 1k v(out)` で THD が出る
- スイープは1ケースずつ実行し、各ログに収束エラーが無いか確認する

## 出力精度

| 経路 | 精度 | 用途 |
|---|---|---|
| 内部 | double (binary64) | 常時 |
| バイナリ raw (`-r` / `write`) | 8 byte/value | 厳密な数値比較 |
| `wrdata` テキスト | `set numdgt=N`、既定9桁 | gnuplot。`numdgt=15` を設定する |
| WAV | 32-bit float (24-bit 仮数) | 音声出力 |

- raw を ASCII にするときは `write` の前に `set filetype=ascii` を置く
- LTspice の .raw / .wave とは非互換
- `wrdata` は `set wr_vecnames` でヘッダ行、`set wr_singlescale` で1スケール + 複数列になる

## WAV 出力

ngspice は WAV を直接書けない。バイナリ raw (float64) を書き、ffmpeg で 32-bit float WAV に変換する。

```spice
.control
run
linearize v(out)
write out.raw v(out)
.endc
```

```sh
# raw は "Binary:\n" の後ろが float64 interleaved (c0=time, c1=信号)
OFF=$(LC_ALL=C grep -abo 'Binary:' out.raw | cut -d: -f1)
tail -c +$((OFF+9)) out.raw | ffmpeg -y -f f64le -ar 96000 -ac 2 -i - \
  -af "pan=mono|c0=c1,volume=1.0" -c:a pcm_f32le out.wav
```

- `linearize` をしないとサンプル間隔が不均一になり `-ar` が成立しない
- `write` にベクトルを列挙しないとプロット内の全ベクトルを書く。列挙しても time が先頭に入るため、ffmpeg は常に 2ch として読み `pan` で c1 を取る
- `-ar` は tstep の逆数と一致させる (既定 96 kHz、`.tran {1/96000}`)
- ngspice 側でスケールせず、音量は `volume` (線形倍率) で調整する。32-bit float は ±1 超えでもクリップしない
- ffmpeg は既定で上書きしないため `-y` を付ける
