---
name: gndless-click-detect
description: Use when checking long 1 kHz sine recordings for clicks/pops, or diagnosing periodic ASRC resync bursts, with click-detect.
---

# Gndless Click-Detect

`click-detect` で長時間録音のクリック/プチノイズを検出する。数分の試聴では気づかない数十分周期のバーストの検出が主目的。

## 使う場面

- ASRC/レート追従まわりの RTL (`FILTER_SHIFT`、レベル補正、FIFO 深さ) を変えた直後の前後比較
- 「音がおかしい」「プチノイズが鳴る」報告の切り分け
- ドリフト補正の長期安定性 (数十分周期のリセットループが出ないか) の確認

## 基本情報

- インストール: `cargo install click-detect`
- ソース: `~/Documents/AkiyukiProjects/dev/mine/click-detect`

## 使い方

```sh
click-detect recording.wav
click-detect recording.flac --export-clicks
```

| オプション | 既定値 | 説明 |
|---|---|---|
| `--cutoff` | 4000 | ハイパスカットオフ Hz |
| `--threshold-mult` | 20 | 包絡線中央値に対する閾値係数 |
| `--min-dbfs` | -80 | 閾値の下限 dBFS |
| `--freq` | 1000 | サイン周波数 Hz |
| `--export-clicks` | - | `clicks.wav` を出力 |
| `--click-pad-ms` | 20 | 抽出の前後パディング ms |

## 結果の解釈

- **Clicks: 0** → 検証パス
- **単発クリック (周期性なし)** → 外部要因 (ソース側の一過性、ケーブル、バッテリー低下など)。1回だけで FPGA/ASRC 起因と断定しない
- **等間隔バースト (CV<5%)** → レートドリフトの一括補正 (ASRC リセット動作) の可能性が高い。クラスタ間隔とクリック数を確認する
  - 実例: 26.7分周期・各50個程度のバースト = トラッカー/レベル補正まわりの定常バイアス
- **起動リセットループ** (無音2ms + フェード11ms + 再生22ms の約35ms周期) → トラッカーの起動過渡が FIFO マージンを超えている。`FILTER_SHIFT` が大きすぎる
  - 過渡ドレイン = 初回測定値の ±640ppm 誤差 × 出力レート × τ (=2^SHIFT/48k)
  - S/MUX2 は出力が 768k/705.6k で通常の2倍になるためドレインも2倍。SHIFT=10 で 96kHz リセットループが実機発生したため SHIFT=8 を採用

## 録音条件

- 1kHz サインを1〜2時間以上録音する
- 録音経路に ASRC (CoreAudio 等) を混ぜない。独立レコーダーへの直接録音が確実
- サイン周波数がずれている場合は `--freq` で指定する

## 検出方法

- 8次バタワース HPF (4kHz、RBJ 式) で1kHz を除去する
- 包絡線 (1ms 移動平均) の適応閾値 (中央値×20、下限 -80dBFS) で検出する
- クリック振幅 = イベント直前2048サンプルへのサイン最小二乗フィットの残差ピーク
- チャンネル0のみ、WAV/FLAC 対応、ストリーミング処理

## 既知の注意

- claxon 0.4.3 の `samples()` はブロック境界で不正な値を返すため、デコードは symphonia を使う
- 短い録音やクリック0件では「サンプル不足で判定不可」と表示される (正常)
