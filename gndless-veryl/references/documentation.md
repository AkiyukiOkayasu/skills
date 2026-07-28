# Documentation comments

Veryl の doc comment を追加・編集する場合に参照する。

## 基本

- Rust の doc comment の慣習を基本とし、公開 module、interface、function、型、port、parameter、const の契約を記載
- 主に自分が使う project では本文を日本語で記載し、それ以外は project の既存方針を優先
- 説明の先頭に役割や基本動作を短くまとめ、parameter の範囲、width、depth、latency、reset、clock domain、memory inference 条件など利用者が必要とする契約を記載
- `Arguments`、`Returns`、`Errors`、`Panics`、`Safety`、`Examples` など簡単な英語の定型見出しは英語で記載
- 1文は必ず1本の `///` 行に収め、読点や節の途中で折り返さない
- 1行あたりの文字数制限を設けず、改行は文・段落・箇条書き・code block など Markdown 上の意味の区切りだけで使用

```veryl
/// 入力を受理した次のサイクルから出力を有効にする。 // correct
/// 入力を受理した次のサイクルから                   // wrong
/// 出力を有効にする。                               // wrong
```

## 日本語

- 簡単な英語の専門用語や短い複合語は英語のまま記載し、`AES3 professional transmitter` を `AES3 professional送信機` のような不自然な和英混在へ変換しない
- 見出しや箇条書きなど1行で完結する記述は末尾に句点を付けず、「〜する」より「〜を確認」「〜を記載」のような体言止めを優先
- 見出しや箇条書き以外の複数行にわたる詳細説明は各文の末尾に句点を付加

## 引数と宣言

- module の `param`、port、function の引数などは、原則として宣言と同じ行の末尾に `///` で記載
- 説明が複数行にわたる場合だけ、宣言直前の複数行 `///` block を許可
- 1行だけの説明を宣言前の独立した行に置かない

```veryl
pub module HpfShiftSigned #(
    param DATA_WIDTH: u32 = 16, /// 入出力データ幅
    param SHIFT     : u32 = 4 , /// シフト量 (1以上)。大きいほど低いカットオフ周波数
) (
    clk   : input  clock                   , /// システムクロック
    rst   : input  reset                   , /// リセット (出力を0に初期化)
    enable: input  bbool                   , /// イネーブル信号 (trueでフィルタ更新)
    x     : input  signed logic<DATA_WIDTH>, /// 入力サンプル (符号付き)
    y     : output signed logic<DATA_WIDTH>, /// フィルタ出力 (符号付き)
) {
}
```

## 図と波形

- `mermaid` と `wavedrom` code block を積極的に使用
- architecture、module 接続、state transition、sequence、transaction は Mermaid を優先
- cycle 動作、ready/valid、request/response、FIFO、pipeline、reset、CDC は WaveDrom を優先
- module port の動作を表せる波形は `wavedrom,test` を積極的に使い、`veryl test` で documentation test を実行
- `veryl doc` で生成結果を確認し、図と波形が実装・契約と一致することを確認

参照: https://doc.veryl-lang.org/book/ja/06_development_environment/10_documentation.html
