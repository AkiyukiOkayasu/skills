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

**注意**: `-retiming` と `-pipe` は `set_option` で設定できるが、`saveto -all_options` の出力に含まれないことがある。必要なら明示的に `set_option` として記述する。

## 新しい Gowin project を立ち上げる手順

### 方法 A: `create_project` を使う

`create_project` でゼロからプロジェクトを作成できる。

**構文**:

```tcl
create_project -name <prjName> -dir <path> -pn <pnName> [-device_version <arg>] [-force]
```

`create_project_example.tcl` をテンプレートとして使い、device / top / file list / pin option を実プロジェクトに合わせて調整する。

### 方法 B: GUI で gprj を作る

1. Gowin IDE で新規プロジェクト作成
2. device を設定
3. ピン制約や device 設定を確認
4. `saveto -all_options` で設定を書き出し、`run_gowin.tcl` のベースにする

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

## 外側のタスクランナーに残すべきもの

- Gowin IDE の絶対パス解決
- `DYLD_LIBRARY_PATH` など実行環境注入
- `gw_sh` 呼び出し
- project ごとの複合 build フロー

Tcl 側は、できるだけ「project をどう開いて何を設定するか」に集中させる。

`just`、`make`、`cargo xtask` など、どのラッパーを使うかはプロジェクト側で決める。

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
- GUI で設定しただけで Tcl に落とさない
- `impl/` 配下の成果物を入力ソースとして扱う
- `run all` で必要になる file list 更新を忘れる
- device 固有 option を説明なしにコピペする
- document に見当たらない挙動だからといって、実機で必要だった reset / boot 対策を消す
