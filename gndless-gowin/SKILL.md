---
name: gndless-gowin
description: Use when working on Gowin-specific project automation and device caveats, including Tcl scripts, gw_sh flows, generated RTL import, project bring-up, and board-specific behaviors that are not obvious from Gowin documentation.
---

# Gndless Gowin

このスキルは、Gowin EDA の Tcl スクリプト、project automation、device 依存の注意点を扱う。

## 使う場面

- 新しい Gowin project を追加したい
- `gw_sh` で再現可能な合成フローを整えたい
- 既存 project を headless 実行できる形にしたい
- Gowin 固有の bring-up 落とし穴を記録したい
- document に載っていない device 挙動を再発防止したい

## 基本方針

- Tcl は IDE のカレントディレクトリに依存させず、`[info script]` 基準で書く
- project path や file list は、なるべく script 相対で解決する
- 生成元は Veryl、合成入口は Gowin project、という責務分離を保つ
- 人手 GUI 操作だけに閉じた手順を残さない
- Gowin 固有の不安定要因や undocumented behavior は、再発防止のため skill に残す

## 独立レビュー

- Tcl、file list、生成RTL、project構成を横断する初期探索、承認済みPlanに沿う明確な自動化修正、手順書の整理、広い差分の巨視的レビューでは、必要に応じて `codex-reviewer` subagentを利用する（読み取り専用、変更はしない）。
- Tcl / `gw_sh` / device errorの追跡、pin・reset・boot・timing optionの詳細設計、生成RTLとの対応、実機依存事項、project設定、最終レビューはopencodeが担当する。

## Gowin 合成の既知制約: interface 配列の procedural for

Gowin Synthesis は、`always_ff` / `always_comb` 内の `for` ループで **interface (modport) 配列要素を変数インデックス選択できない**。

- エラー例: `ERROR (EX3812) : 'i' is not a constant` (Veryl の interface が生成する SV の配列要素アクセスが定数展開されない)
- 定数インデックス (`channels[0].raw` など) は procedural 内でも合成できる。問題になるのは変数 `i` を使うループだけ
- この制約は Veryl の `veryl check` / `veryl test` では検出されず、Gowin 合成でのみ失敗する

**回避パターン** (Veryl):

- 入力 interface は generate assign で raw の plain 配列へ展開し、procedural 内は plain 配列を扱う

```veryl
var i_channels_raw: gndless_fixedpoint::Q1_23::Raw [8];
for i in 0..8 :g_ich {
    assign i_channels_raw[i] = i_channels[i].raw;
}
```

- 出力 interface も同様に、内部 plain 配列から generate assign で接続する

```veryl
for i in 0..8 :g_out {
    assign o_channels[i].raw = o_channels_raw[i];
}
```

- testbench (合成対象外) の `.raw` アクセスには適用不要

## PnR 配置・ルーティングオプション (`-place_option` / `-route_option`)

タイミングマージンが足りないとき、合成オプション (`-retiming` / `-pipe` / `-route_maxfan`) で
改善しない場合は、**PnR の配置・ルーティングアルゴリズム選択**を試す。

- `-place_option 2`: timing 優先の配置。単独で改善することが多い
- `-place_option 3` / `4`: 複数試行から最良を選択 (詳細は未公開)。**3 + `-route_option 1` の
  組み合わせが実測で最も良い** (FPGA_Oscillator で Fmax 50.4 → 62.6 MHz)
- `-route_option 1`: timing に従うルーティング

**注意 (cmd.do の永続化)**: PnR 設定は `impl/pnr/cmd.do` に保存され、オプション変更が
反映されないことがある。`set_option` を変更したら **`impl/pnr/cmd.do` を削除して再実行**する。
詳細は [references/pnr-placement-options.md](references/pnr-placement-options.md)。

## Gowin 固有の注意を残す基準

- Gowin document に明記されていない
- 一度ハマると再発コストが高い
- RTL / reset / memory / boot のような基盤挙動に関わる
- Tcl だけ見ても理由が分からない

この条件に当てはまるなら、README から消しても skill には残す。

## 既存スクリプトから引き継ぐべき要点

- `set script_path [file normalize [info script]]`
- `set script_dir [file dirname $script_path]`
- project は `file join` で組み立てる
- `open_project` 後に `set_option` を明示する
- `import_files -fileList ... -force` で最新生成物を再投入する
- `run all` + `run close` まで含めて自動化する
- `run close` で gprj に変更を保存する（`run all` だけでは保存されない）

## `saveto` で現在の全設定を確認する

`run_gowin.tcl` に漏れがないか確認するには、`saveto -all_options` を使う。

```tcl
open_project myProject/myProject.gprj
saveto -all_options project_config.tcl
run close
```

出力された `project_config.tcl` と現在の `run_gowin.tcl` を比較し、不足している `set_option` を洗い出す。

**注意**: `-retiming` / `-pipe` は **headless gw_sh フローでは no-op** (V1.9.12 で検証)。
GUI の設定定義 (synthesisoptions.xml の SYN13 Retiming / SYN12 Pipelining、retiming デフォルト 1) には
存在するが、`set_option` で設定しても合成ネットリストは変化しない (タイムスタンプヘッダを除いた
hash 比較で確認。3組み合わせすべて同一)。公式 Tcl ガイド (SUG1220) にも `saveto -all_options` にも
gprj にも現れない。**tcl から削除してよい** (`-route_maxfan` は PnR の `cmd.do` に現れる実オプション
なので残すこと)。

## 新しい Gowin project を立ち上げる手順

`create_project` でゼロからプロジェクトを作成できる。

**構文**:

```tcl
create_project -name <prjName> -dir <path> -pn <pnName> [-device_version <arg>] [-force]
```

`create_project_example.tcl` をテンプレートとして使い、device / top / file list / pin option を実プロジェクトに合わせて調整する。

## Tcl テンプレート

```tcl
set script_path [file normalize [info script]]
set script_dir [file dirname $script_path]
set project_path [file join $script_dir "myProject/myProject.gprj"]
set filelist_path [file join $script_dir "../RTL/Veryl_MyTarget/my_target.f"]

puts "Opening project: $project_path"
open_project $project_path

puts "Setting SystemVerilog 2017 mode..."
set_option -verilog_std sysv2017

puts "Setting top module..."
set_option -top_module my_top

puts "Timing-driven synthesis options..."
set_option -timing_driven 1
set_option -correct_hold_violation 1
set_option -route_maxfan 50
set_option -retiming 1
set_option -pipe 1

puts "IOB register packing..."
set_option -ireg_in_iob 1
set_option -oreg_in_iob 1
set_option -ioreg_in_iob 1

puts "Multi-purpose pin config..."
set_option -use_cpu_as_gpio 1
set_option -use_ready_as_gpio 1
set_option -use_jtag_as_gpio 0
set_option -use_sspi_as_gpio 1
set_option -use_mspi_as_gpio 0
set_option -use_done_as_gpio 0
set_option -use_mode_as_gpio 0
set_option -use_i2c_as_gpio 0

puts "Constraint settings..."
set_option -cst_warn_to_error 1

puts "Bitstream settings..."
set_option -bit_format bin
set_option -bit_security 1
set_option -bit_incl_bsram_init 1
set_option -loading_rate default

puts "MultiBoot settings..."
set_option -multi_boot 0
set_option -mspi_jump 0

puts "Importing generated RTL..."
import_files -fileList $filelist_path -force

puts "Running synthesis..."
run all

puts "Closing and saving project..."
run close
```

## Tcl の外側で扱うもの

- Gowin IDE の絶対パス解決
- `DYLD_LIBRARY_PATH` など実行環境注入
- `gw_sh` 呼び出し
- project ごとの複合 build フロー

Tcl 側は、できるだけ「project をどう開いて何を設定するか」に集中させる。

## プロジェクト固有事項

- board 固有 pin option、MultiBoot 運用、reset delay、flash address、build wrapper はプロジェクト側の skill に置く
- 特定ボードの雛形が必要なら、この skill をベースに別 skill へ切り出す

## project 新設時の確認項目

- device が正しいか
- top module 名が一致しているか
- `import_files` の file list が最新の生成物を向いているか
- JTAG / READY / CPU / MSPI など特殊 pin option が用途に合っているか
- MultiBoot を使うなら address 幅と flash address が正しいか
- Background programming (`-bg_programming`) が必要か
- BSRAM や boot 周辺の安定化に reset delay が必要か
- reset 方針を変えるなら、実機起動確認なしに削らないか
- `run close` で gprj を保存しているか
- `saveto -all_options` で設定漏れを確認したか

## アンチパターン

- `cd` 前提の相対パスで script を書く
- `impl/` 配下の成果物を入力ソースとして扱う
- `run all` で必要になる file list 更新を忘れる
- device 固有 option を説明なしにコピペする
- document に見当たらない挙動だからといって、実機で必要だった reset / boot 対策を消す
