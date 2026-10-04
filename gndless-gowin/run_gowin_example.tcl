# 既存 Gowin project を開いて合成する run_gowin.tcl のテンプレート
# 使い方:
#   1. project_path / filelist_path / top module / pin option を実プロジェクトに合わせる
#   2. ./gw_sh run_gowin_example.tcl で実行
# 注意:
#   - -retiming / -pipe は headless gw_sh では no-op なので含めない
#   - run all だけでは gprj に保存されないため、run close まで実行する
#   - PnR 設定 (-place_option / -route_option) を変えたら impl/pnr/cmd.do を削除してから再実行する

set script_path [file normalize [info script]]
set script_dir [file dirname $script_path]
set project_path [file join $script_dir "myProject/myProject.gprj"]
set filelist_path [file join $script_dir "../RTL/Veryl_MyTarget/my_target.f"]

open_project $project_path

set_option -verilog_std sysv2017
set_option -top_module my_top

# timing-driven synthesis
set_option -timing_driven 1
set_option -correct_hold_violation 1
set_option -route_maxfan 50

# IOB register packing
set_option -ireg_in_iob 1
set_option -oreg_in_iob 1
set_option -ioreg_in_iob 1

# multi-purpose pins
set_option -use_cpu_as_gpio 1
set_option -use_ready_as_gpio 1
set_option -use_jtag_as_gpio 0
set_option -use_sspi_as_gpio 1
set_option -use_mspi_as_gpio 0
set_option -use_done_as_gpio 0
set_option -use_mode_as_gpio 0
set_option -use_i2c_as_gpio 0

# constraints / bitstream
set_option -cst_warn_to_error 1
set_option -bit_format bin
set_option -bit_security 1
set_option -bit_incl_bsram_init 1
set_option -loading_rate default

# multiboot
set_option -multi_boot 0
set_option -mspi_jump 0

import_files -fileList $filelist_path -force
run all
run close
