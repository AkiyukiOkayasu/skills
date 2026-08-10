---
name: gndless-click-detect
description: Use when verifying long 1 kHz sine recordings for clicks/pops in ADAT/ASRC hardware bring-up — for example after changing rate-tracking parameters, when click noise is reported, or for long-term stability checks — and when diagnosing periodic burst artifacts (rate-drift resync) in sample-rate-conversion chains.
---

# Gndless Click-Detect

1kHzサイン波の長時間録音にクリック/プチノイズが含まれていないかを検証するCLIツール`click-detect`の使い方と結果の解釈を扱う。

## 使う場面

以下のような「録音にクリックが混ざっていないか」を確かめたい場面で使う。数分の試聴では気づかない長周期ノイズ(数十分周期のバースト)の検出が主目的。

- **ASRC/レート追従まわりのRTLを変更した直後**: `FILTER_SHIFT`やレベル補正、FIFO深さなどを変えたら、変更前後で同じ録音手順の1〜2時間録音を比較し、バーストが新規発生していないか確認する
- **「音がおかしい」「プチノイズが鳴る」という報告を受けたとき**: 再現録音を解析して、クリックが実在するか・等間隔バーストか・単発かを切り分ける。等間隔ならASRCのドリフト補正(リセット動作)、単発なら外部要因(ソース/ケーブル/バッテリー等)の可能性が高い
- **長時間安定性の確認**: ドリフト補正が正しく機能していること(数十分周期のリセットループが出ないこと)を、1〜2時間以上の録音で自動検証する
- **録音セットアップの切り分け**: クロック同期の有無や録音経路(独立レコーダー vs PCオーディオ経由)を変えたとき、ノイズ源がFPGA側か測定系側かを比較する
- **新しい録音を受け取ったときの定型チェック**: クリック有無・ピーク分布・時間別分布を一覧化して、前回の状態と差分を確認する
- **バグ修正の回帰確認**: 修正前後で「クリック0件」が維持されていることを記録として残す

## 基本情報

- インストール: `cargo install click-detect`
- ソース: `~/Documents/AkiyukiProjects/dev/mine/click-detect`(crates.io公開・GitHub `AkiyukiOkayasu/click-detect`)
- Python版は廃止済み(Rust版v0.1.1へ置き換え)。`Tools/click_detector.py`は削除済み

## 使い方

```sh
click-detect recording.wav
click-detect recording.flac --export-clicks    # クリック抽出WAVも出力
```

| オプション | 既定値 | 説明 |
|---|---|---|
| `--cutoff` | 4000 | ハイパスカットオフHz |
| `--threshold-mult` | 20 | 包絡線中央値に対する閾値係数 |
| `--min-dbfs` | -80 | 閾値の下限dBFS |
| `--freq` | 1000 | サイン周波数Hz |
| `--export-clicks` | - | `clicks.wav`(前後20ms+100ms無音)を出力 |
| `--click-pad-ms` | 20 | 抽出の前後パディングms |

## 出力の解釈

- **Clicks: 0** → クリックなし。検証パス
- **単発クリック(周期性なし)** → 外部要因(ソース側の一過性・ケーブル・バッテリー低下など)。1回だけではFPGA/ASRC起因と断定しない
- **等間隔バースト(CV<5%)** → レートドリフトの一括補正(ASRCリセット動作)の可能性が高い。クラスタ間隔とクリック数をCSVで確認
  - 実例: 26.7分周期・各50個程度のバースト = トラッカー/レベル補正まわりの定常バイアス
- **起動リセットループ**(無音2ms+フェード11ms+再生22msの約35ms周期) → トラッカーの起動過渡がFIFOマージンを超えている。`FILTER_SHIFT`が大きすぎる
  - 過渡ドレイン = 初回測定値の±640ppm誤差 × 出力レート × τ(=2^SHIFT/48k)
  - S/MUX2は出力が768k/705.6kで通常の2倍 → ドレインも2倍。SHIFT=10で96kHzリセットループが実機発生したためSHIFT=8を採用

## 録音条件の推奨

- 1kHzサインを1〜2時間以上録音する(数分の試聴では見逃す長周期ノイズが対象)
- 録音経路にASRC(CoreAudio等)を混ぜない。独立レコーダーへの直接録音が確実
- サインの周波数がずれている場合は`--freq`で指定

## 検出手法の要点(結果解釈の前提)

- 8次バタワースHPF(4kHz・RBJ式、scipy `butter`と一致)で1kHzを除去
- 包絡線(1ms移動平均)の適応閾値(中央値×20、下限-80dBFS)で検出
- クリック振幅 = イベント直前2048サンプルへのサイン最小二乗フィットの残差ピーク
- チャンネル0のみ・WAV/FLAC対応・ストリーミング処理(入力全体を保持しない)

## 既知の注意

- claxon 0.4.3の`samples()`はブロック境界で不正な値を返すため、デコードはsymphoniaを使う
- 短い録音やクリック0件では「サンプル不足で判定不可」と表示される(正常)
