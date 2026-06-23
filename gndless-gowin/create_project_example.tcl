# Gowin プロジェクト作成テンプレート
# 使い方:
#   1. PROJECT_NAME, DEVICE_PN, DEVICE_VERSION, TOP_MODULE を変更
#   2. 必要なら pin / bitstream / multiboot option を調整
#   3. gw_sh で実行: ./gw_sh create_project_example.tcl

set script_path [file normalize [info script]]
set script_dir [file dirname $script_path]

# === ユーザー設定ここから ===
set PROJECT_NAME "myProject"
set DIR "$script_dir/$PROJECT_NAME"
set DEVICE_PN "GW5A-LV25MG121NC1/I0"
set DEVICE_VERSION "A"
set TOP_MODULE "my_top"
# === ユーザー設定ここまで ===

puts "Creating project: $PROJECT_NAME"
create_project -name $PROJECT_NAME -dir $DIR -pn $DEVICE_PN -device_version $DEVICE_VERSION -force

puts "Setting SystemVerilog 2017 mode..."
set_option -verilog_std sysv2017

puts "Setting top module..."
set_option -top_module $TOP_MODULE

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

puts "Project created: $DIR/$PROJECT_NAME.gprj"
puts "Next step: import_files -fileList <generated_filelist.f> -force"
puts "Then: run all"
puts "Then: run close"
