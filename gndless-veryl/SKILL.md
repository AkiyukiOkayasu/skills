---
name: gndless-veryl
description: Use when editing Veryl RTL, configuring Veryl projects, updating generated RTL, or selecting the appropriate Veryl verification flow.
---

# Gndless Veryl

Veryl RTLの編集、検証、生成RTLの更新を扱う。対象は`.veryl`、`Veryl.toml`、Verylのtest、生成RTLの更新である。

## 基本方針

- まずproject固有の`Veryl.toml`、toolchain、下流build script、他のskillを確認する。
- Verylは1.0未満でspec・standard library APIが変わり得る。update時はrelease noteとmigration結果を確認するが、旧versionとのcompatibilityを過度に維持しない。
- 編集対象は`.veryl`を正とする。`target/`などの生成`.sv`、`.sv.map`、`.f`を手で直さない。
- Verylの短い構文ではなく、生成回路のwire/register、bit width、signedness、mux・logic depth、RAM/FF inference、reset cost、clock domainを確認する。

## Workflow

`.veryl`を変更したら、対象projectで原則として次を実行する。

```text
veryl fmt --check
veryl check
veryl test
veryl build
```

- format変更には`veryl fmt`を使う。
- 小さなunit testは`veryl test`とnative testを優先する。長いtestは通常skipし、必要時だけ`veryl test --ignored`を使う。
- built-in simulatorのbackend差を確認する場合は`veryl test --backend-validate`を使う。`--wave`は失敗の再現・波形解析時に限定する。
- native testで表現しにくいsystem-level検証だけ、project側で定義された外部simulation workflowを併用する。
- `veryl synth`は設計探索用の概算であり、vendor synthesis、place-and-route、timing sign-offの代替にしない。
- Veryl更新時は`veryl migrate --check`を先に実行する。migrationを実行した場合は`fmt`、`check`、`test`、`build`後にVerylと生成RTLのdiffを確認する。

## Naming and types

- projectの既存規約を優先する。規約がなければ、fileは`snake_case`、public module/interfaceは`UpperCamelCase`、function/local/instance/portは`snake_case`、param/constは`UPPER_SNAKE_CASE`、packageは`PascalCase`を使う。
- portは`i_`/`o_`や`_in`/`_out`を付けず、意味名を使う。Verylでは`input`/`output`が型として表現できるため、prefixは不要と判断する。std interfaceの既定名は例外とする。
- clock portは`clk`、system reset portは`rst`を原則とする。Verylのreserved word`clock`/`reset`をidentifierとして使う必要がある場合のみ、`r#clock`/`r#reset`でescapeする。functional resetはsemantic nameを使い、typeはBoolean typeの指針で判断する。設計上2値のBoolean controlなら`bbool`、`x/z`を保持・伝播する必要があれば`lbool`、bit vectorやprotocol signalなら`logic`とする。
- public port、module契約、register width、accumulator width、signednessが重要な境界では型を省略しない。型推論は内部の短い式に限定する。
- `logic<W>`はpacked、`[N]`はunpacked。address、index、count、pointer、byte offsetを同じ意味として扱わない。
- FSMはenum、pipelineやbusの関連信号はstructで束ねる。ただしpublic transactionとinternal transactionを分離し、巨大なstructでmoduleを密結合にしない。
- 外部からoverrideする値は`param`、内部で導出する値は`const`にする。parameterの範囲、対応するdepth、width、latency、memory inference条件をmodule documentationに書く。

## Cast

- `as 32`のように、`as`の後ろにはwidthを指定してcastする。
- `as logic<32>`や`as bit<32>`のように型名を書くのは誤り。
- `as`でsigned/unsignedの属性は変わらない。
- 値をsignedとして扱うときはsystem function`$signed()`を使う。
- `$signed()`は「signedとして扱う」だけで、sign bitを勝手に書き換えない。

Correct / incorrect examples:

```veryl
let a: logic<32> = value as 32;          // correct
let b: logic<32> = value as logic<32>;   // wrong
let c: logic<32> = value as bit<32>;     // wrong
let d: i32       = $signed(value as 32); // signed として扱いたい場合
```

Rule:

- `as`の右側にはtypeではなくwidthを書く。
- signed/unsignedを変えたいなら`as`ではなく`$signed()`を使う。

## System functions / system tasks

VerylではSystemVerilog標準のsystem function / system taskを使える。

- `$clog2(x)`は`x`のlog2の切り上げ。
- `$size(x)`はarray size。
- `$bits(x)`はvalueのbit width。
- `$signed(x)`はvalueをsignedとして扱う。
- `$readmemh(path, mem)`はhex fileをmemoryへ読み込む。
- `$display(...)`はstring output。
- `$error(...)`はerror output。
- `$finish()`はsimulationを終了する。

使用例:

```veryl
const w1: u32 = $clog2(32); // 5
const w2: u32 = $clog2(35); // 6

var array: logic<4, 8>;
const s1: u32 = $size(array); // 4
const s2: u32 = $bits(array); // 32

var uvalue: u32;
let svalue: i32 = $signed(uvalue) + 1;

initial {
    $readmemh("file.hex", array);
    $display("Hello World!");
    $error("Error!");
    $finish();
}
```

## Boolean type

- `bbool`は`bit<1>`のBoolean type alias。
- `lbool`は`logic<1>`のBoolean type alias。
- `true`と`false`も使える。
- 型の本質的な差は、`bbool`が2値（`0/1`）、`lbool`が4値（`0/1/x/z`）であること。
- `bbool`は、(1)設計上0/1だけを保証でき、(2)Boolean value（`true`/`false`）として表現でき、(3)`bbool`にすることで意図の可読性が高まるsignal/valueに使う。param、const、input、output、internal register、function return value、struct fieldを区別しない。
- `lbool`は「意味はBooleanだが、未初期化・CDC・external inputなどによる`x/z`を保持して伝播させたい」場合に使う。
- `logic`は、Booleanではなく1bitのencoding・waveform・protocol signalとして扱うvalue、または`x/z`を検証で観測したいvalueに使う。0/1しか現れないraw serial bitでも、`true`/`false`よりbit valueとして読む方が自然なら`logic`のままにする。
- `enable`、`reset`、`copy_permitted`、`non_audio`、`original`、`invalid`、`locked`、`error`などはnameだけで決めず、設計上`x/z`が合法か、初期化後に必ず0/1になるかを確認する。
- `true`/`false`を使えることと、型を`bbool`/`lbool`にすることは別。信号名だけで型を変えない。
- `logic`から`bbool`への変換は`x/z`を失うため、暗黙変換や一括置換を避け、2値化が仕様であることを確認する。
- 公式stdの用例は参考にするが、SystemVerilog互換やstd内の採用箇所をtype選択の上限にしない。
- 参照: https://doc.veryl-lang.org/book/05_language_reference/03_data_type/01_builtin_type.html
- 参照: https://std.veryl-lang.org/async_fifo.html

## RTL記述の規約

- `always_comb`はoutputとnext-stateへ先頭でdefault assignmentを置き、全経路で代入する。latch、長いpriority chain、組み合わせloopを避ける。
- `always_ff`内の`=`はnonblocking相当へ変換される。各registerにownerを一つだけ置き、reset、flush、stall、通常更新、holdの優先順位を明示する。
- `valid`とpayload、FIFO pointerとcount、requestの各fieldなど同じtransactionに属する状態は同じ更新規則で扱う。stall中にpayloadだけ、flush時にvalidだけがずれないようにする。
- FSMはstate registerとnext-state logicを分離し、反復回数はstateを増やさずcounterで表す。illegal stateの復帰またはassertion方針を決める。
- `gen`/generateはlane、bank、stageなどの構造複製に限定する。runtime loopと混同しない。非2冪depthを許す場合はpointerのwrapを明示する。

## Clock、reset、CDC

- clock/reset型と`if_reset`を使い、極性・同期性を設定と契約で管理する。単一clock/resetの省略記法は小さな単一domain moduleに限定し、複数domain、derived/test/scan clock、async FIFO、synchronizer周辺では対象を明示する。
- resetは無料ではない。FSM、valid、protocol-visible state、software-visible stateなど既知値が必要なものに限定し、memory array、valid=0中に参照しないpayload、RAM/BRAMへ不要なresetを付けない。
- abstract resetを使っても同期reset・非同期resetのtimingやFPGA primitiveへのmappingの差は消えない。採用したreset構成で検証する。
- clock-domain annotationや`unsafe (cdc)`は意図を示すだけで、CDC回路やmetastability対策を生成しない。single-bitはsynchronizer、pulseはtoggle/handshake、multi-bit streamはasync FIFOなど、実回路を実装して検証する。

## interface、FIFO、memory

- ready/validの転送条件は`valid && ready`。送信側はtransferまでvalidとdataを保持し、受信側はtransfer時だけ状態を進める。backpressure、flush、latency、outstanding transactionを契約に書く。
- request acceptanceとresponse completionを分離する。ready/validをmodule間で相互に組み合わせ依存させず、必要ならregisterまたはskid bufferでloopを切る。
- FIFOはstorage、pointer、count/phase、empty/full、同時push/pop、full/empty時の挙動を明示する。fall-through、同期read、registered outputなどの出力方式とlatencyを隠さない。
- memoryは実装前に1R1W/1RW/2RW、read latency、read-during-write、byte enable、初期化、FPGA BRAM推論条件を決める。組み合わせreadを前提にして後から同期RAMへ置換しない。
- 大容量arrayは原則resetせず、valid bit、tag/epoch、初期化sequenceで無効状態を管理する。FPGA vendor primitiveはwrapperへ隔離し、上位Veryl moduleから直接参照しない。

## fixed-point・DSP

- format（total width、integer/fraction bits、signedness）、rounding、overflow、latency、stall/backpressureをmodule契約に含める。
- 加算・乗算・accumulatorは必要な拡張幅とguard bitを確保する。丸めは十分広い値のまま行い、その後にsaturationまたは明示的truncationを行う。先に幅を切ってoverflow情報を失わない。

## 検証と生成RTL

- 検証はcomb function → 小さなsequential primitive → FIFO/RAM → protocol adapter → subsystem → topの順に小さく分ける。
- module boundaryにvalid安定、full/empty、alignment、one-hot、illegal opcode、grant排他などのcontract assertionを置く。
- native testは高速unit testの基本とする。signed arithmetic、X/Z、memory read-during-write、generated clock、async reset、simulator依存system functionはreference modelやproject側のsystem-level testでもcross-checkする。
- 波形は通常testで常時生成せず、失敗再現時に対象signalを絞って保存する。
- 下流EDAが返す生成RTLの行番号はsource mapでVerylへ戻す。生成RTL、filelist、module hierarchyのdiffもtoolchain更新時に確認する。
- FPGAではvendor primitiveを隔離し、低速処理は新しいderived clockよりclock enableを優先する。合成後にBRAM、DSP、carry、LUTなどのinference結果をreportで確認する。

## 依存関係とpublish

- 依存関係・標準libraryはVerylの公開API変更を前提に扱い、必要なら更新後の生成RTLとtest結果を確認する。
- publishは次の順序を守る。
  1. `Veryl.toml`のversionを更新し、その変更だけをcommitする。
  2. `veryl publish`を実行する。
  3. `Veryl.pub`のversionとcommit対応を確認し、`Veryl.pub`だけを別commitする。
- `Veryl.toml`と`Veryl.pub`を同じcommitにまとめない。publish前に対象commitの状態を確定する。

## Anti-patterns

- 生成物を直接編集する。
- `veryl check`を通さずにRTLや契約信号を変更する。
- `unsafe (cdc)`だけでCDCを完了したとみなす。
- memory arrayを全resetしてRAM/BRAM推論を壊す。
- implicit truncation、signedness、parameter範囲、memory latencyを未定義のままにする。
- validとpayload、stallとflushの更新を別々にしてtransactionを壊す。
- 小さな性質確認に最初から重いtestbenchを作る、またはnative testだけでsystem-level correctnessを済ませる。
- vendor primitive、register map、Fmax、board flow、project-specificな統合条件をこのskillへ持ち込む。これらはproject側のskillに置く。
