; ModuleID = "scriptum"
source_filename = "scriptum"
%scriptum.value = type { i32, double, i32, i32, i8* }
%scriptum.text = type { i64, i64, i8* }
%scriptum.array = type { i64, i64, i64, %scriptum.value* }
%scriptum.object.entry = type { %scriptum.text*, %scriptum.value }
%scriptum.object = type { i64, i64, i64, %scriptum.object.entry* }
%scriptum.lambda = type { i64, %scriptum.value (i8*, %scriptum.value*, i64)*, i8* }
%scriptum.optional = type { i64, i8, [7 x i8], %scriptum.value }

declare i8* @scriptum_alloc(i64)
declare %scriptum.value @scriptum_value_number(double)
declare %scriptum.value @scriptum_value_boolean(i32)
declare %scriptum.value @scriptum_value_null()
declare %scriptum.value @scriptum_value_text(%scriptum.text*)
declare %scriptum.value @scriptum_value_array(%scriptum.array*)
declare %scriptum.value @scriptum_value_object(%scriptum.object*)
declare %scriptum.value @scriptum_value_lambda(%scriptum.lambda*)
declare double @scriptum_value_as_number(%scriptum.value*)
declare i32 @scriptum_value_as_boolean(%scriptum.value*)
declare %scriptum.text* @scriptum_value_expect_text(%scriptum.value*)
declare %scriptum.array* @scriptum_value_expect_array(%scriptum.value*)
declare %scriptum.object* @scriptum_value_expect_object(%scriptum.value*)
declare %scriptum.lambda* @scriptum_value_expect_lambda(%scriptum.value*)

declare %scriptum.text* @scriptum_text_new(i8*, i64)
declare void @scriptum_text_release(%scriptum.text*)
declare %scriptum.array* @scriptum_array_new(i64)
declare void @scriptum_array_push(%scriptum.array*, %scriptum.value)
declare i64 @scriptum_array_len(%scriptum.array*)
declare i32 @scriptum_array_get(%scriptum.array*, i64, %scriptum.value*)
declare %scriptum.object* @scriptum_object_new()
declare void @scriptum_object_set(%scriptum.object*, %scriptum.text*, %scriptum.value)
declare %scriptum.optional* @scriptum_optional_new(%scriptum.value)
declare %scriptum.value @scriptum_optional_or_else(%scriptum.optional*, %scriptum.value)
declare %scriptum.lambda* @scriptum_lambda_new(%scriptum.value (i8*, %scriptum.value*, i64)*, i8*)
declare void @scriptum_lambda_retain(%scriptum.lambda*)
declare void @scriptum_lambda_release(%scriptum.lambda*)
declare %scriptum.value @scriptum_lambda_call(%scriptum.lambda*, %scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_scribe(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_longitudo(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_numerus(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_textus(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_booleanum(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_ambitus(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_summa(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_minimum(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_maximum(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_absolutum(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_aliquod(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_omnia(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_lege(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_enumera(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_coniunge(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_applica(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_filtra(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_ordina(%scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_array_adde(%scriptum.array*, %scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_array_exime(%scriptum.array*, %scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_array_extende(%scriptum.array*, %scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_array_inserta(%scriptum.array*, %scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_array_remove(%scriptum.array*, %scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_array_purga(%scriptum.array*, %scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_text_divide(%scriptum.text*, %scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_text_coniunge(%scriptum.text*, %scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_text_substitue(%scriptum.text*, %scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_text_ad_minusculas(%scriptum.text*, %scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_text_ad_maiusculas(%scriptum.text*, %scriptum.value*, i64)
declare %scriptum.value @scriptum_rt_text_abscinde(%scriptum.text*, %scriptum.value*, i64)
@.str.0 = private unnamed_addr constant [6 x i8] c"\61\2C\62\2C\63\00"
@.str.1 = private unnamed_addr constant [2 x i8] c"\2C\00"
@.str.2 = private unnamed_addr constant [3 x i8] c"\2C\20\00"
@.str.3 = private unnamed_addr constant [2 x i8] c"\61\00"
@.str.4 = private unnamed_addr constant [2 x i8] c"\78\00"
define %scriptum.value @principalis() {
entry:
  %xs.slot1 = alloca %scriptum.value
  %null2 = call %scriptum.value @scriptum_value_null()
  %array.new3 = call %scriptum.array* @scriptum_array_new(i64 2)
  %num4 = call %scriptum.value @scriptum_value_number(double 1.0)
  call void @scriptum_array_push(%scriptum.array* %array.new3, %scriptum.value %num4)
  %num5 = call %scriptum.value @scriptum_value_number(double 2.0)
  call void @scriptum_array_push(%scriptum.array* %array.new3, %scriptum.value %num5)
  %array.wrap6 = call %scriptum.value @scriptum_value_array(%scriptum.array* %array.new3)
  store %scriptum.value %array.wrap6, %scriptum.value* %xs.slot1
  %load7 = load %scriptum.value, %scriptum.value* %xs.slot1
  %num8 = call %scriptum.value @scriptum_value_number(double 3.0)
  %spill9 = alloca %scriptum.value
  store %scriptum.value %load7, %scriptum.value* %spill9
  %array.ptr10 = call %scriptum.array* @scriptum_value_expect_array(%scriptum.value* %spill9)
  %adde.args11 = alloca %scriptum.value, i64 1
  %adde.arg.slot12 = getelementptr inbounds %scriptum.value, %scriptum.value* %adde.args11, i64 0
  store %scriptum.value %num8, %scriptum.value* %adde.arg.slot12
  %adde.method13 = call %scriptum.value @scriptum_rt_array_adde(%scriptum.array* %array.ptr10, %scriptum.value* %adde.args11, i64 1)
  %load14 = load %scriptum.value, %scriptum.value* %xs.slot1
  %array.new15 = call %scriptum.array* @scriptum_array_new(i64 2)
  %num16 = call %scriptum.value @scriptum_value_number(double 4.0)
  call void @scriptum_array_push(%scriptum.array* %array.new15, %scriptum.value %num16)
  %num17 = call %scriptum.value @scriptum_value_number(double 5.0)
  call void @scriptum_array_push(%scriptum.array* %array.new15, %scriptum.value %num17)
  %array.wrap18 = call %scriptum.value @scriptum_value_array(%scriptum.array* %array.new15)
  %spill19 = alloca %scriptum.value
  store %scriptum.value %load14, %scriptum.value* %spill19
  %array.ptr20 = call %scriptum.array* @scriptum_value_expect_array(%scriptum.value* %spill19)
  %extende.args21 = alloca %scriptum.value, i64 1
  %extende.arg.slot22 = getelementptr inbounds %scriptum.value, %scriptum.value* %extende.args21, i64 0
  store %scriptum.value %array.wrap18, %scriptum.value* %extende.arg.slot22
  %extende.method23 = call %scriptum.value @scriptum_rt_array_extende(%scriptum.array* %array.ptr20, %scriptum.value* %extende.args21, i64 1)
  %load24 = load %scriptum.value, %scriptum.value* %xs.slot1
  %num25 = call %scriptum.value @scriptum_value_number(double 0.0)
  %num26 = call %scriptum.value @scriptum_value_number(double 0.0)
  %spill27 = alloca %scriptum.value
  store %scriptum.value %load24, %scriptum.value* %spill27
  %array.ptr28 = call %scriptum.array* @scriptum_value_expect_array(%scriptum.value* %spill27)
  %inserta.args29 = alloca %scriptum.value, i64 2
  %inserta.arg.slot30 = getelementptr inbounds %scriptum.value, %scriptum.value* %inserta.args29, i64 0
  store %scriptum.value %num25, %scriptum.value* %inserta.arg.slot30
  %inserta.arg.slot31 = getelementptr inbounds %scriptum.value, %scriptum.value* %inserta.args29, i64 1
  store %scriptum.value %num26, %scriptum.value* %inserta.arg.slot31
  %inserta.method32 = call %scriptum.value @scriptum_rt_array_inserta(%scriptum.array* %array.ptr28, %scriptum.value* %inserta.args29, i64 2)
  %load33 = load %scriptum.value, %scriptum.value* %xs.slot1
  %num34 = call %scriptum.value @scriptum_value_number(double 2.0)
  %spill35 = alloca %scriptum.value
  store %scriptum.value %load33, %scriptum.value* %spill35
  %array.ptr36 = call %scriptum.array* @scriptum_value_expect_array(%scriptum.value* %spill35)
  %remove.args37 = alloca %scriptum.value, i64 1
  %remove.arg.slot38 = getelementptr inbounds %scriptum.value, %scriptum.value* %remove.args37, i64 0
  store %scriptum.value %num34, %scriptum.value* %remove.arg.slot38
  %remove.method39 = call %scriptum.value @scriptum_rt_array_remove(%scriptum.array* %array.ptr36, %scriptum.value* %remove.args37, i64 1)
  %load40 = load %scriptum.value, %scriptum.value* %xs.slot1
  %spill41 = alloca %scriptum.value
  store %scriptum.value %load40, %scriptum.value* %spill41
  %array.ptr42 = call %scriptum.array* @scriptum_value_expect_array(%scriptum.value* %spill41)
  %purga.method43 = call %scriptum.value @scriptum_rt_array_purga(%scriptum.array* %array.ptr42, %scriptum.value* null, i64 0)
  %load44 = load %scriptum.value, %scriptum.value* %xs.slot1
  %num45 = call %scriptum.value @scriptum_value_number(double 9.0)
  %spill46 = alloca %scriptum.value
  store %scriptum.value %load44, %scriptum.value* %spill46
  %array.ptr47 = call %scriptum.array* @scriptum_value_expect_array(%scriptum.value* %spill46)
  %adde.args48 = alloca %scriptum.value, i64 1
  %adde.arg.slot49 = getelementptr inbounds %scriptum.value, %scriptum.value* %adde.args48, i64 0
  store %scriptum.value %num45, %scriptum.value* %adde.arg.slot49
  %adde.method50 = call %scriptum.value @scriptum_rt_array_adde(%scriptum.array* %array.ptr47, %scriptum.value* %adde.args48, i64 1)
  %partes.slot51 = alloca %scriptum.value
  %null52 = call %scriptum.value @scriptum_value_null()
  %text.data53 = getelementptr inbounds [6 x i8], [6 x i8]* @.str.0, i32 0, i32 0
  %text.new54 = call %scriptum.text* @scriptum_text_new(i8* %text.data53, i64 5)
  %str55 = call %scriptum.value @scriptum_value_text(%scriptum.text* %text.new54)
  %text.data56 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.1, i32 0, i32 0
  %text.new57 = call %scriptum.text* @scriptum_text_new(i8* %text.data56, i64 1)
  %str58 = call %scriptum.value @scriptum_value_text(%scriptum.text* %text.new57)
  %spill59 = alloca %scriptum.value
  store %scriptum.value %str55, %scriptum.value* %spill59
  %text.ptr60 = call %scriptum.text* @scriptum_value_expect_text(%scriptum.value* %spill59)
  %divide.args61 = alloca %scriptum.value, i64 1
  %divide.arg.slot62 = getelementptr inbounds %scriptum.value, %scriptum.value* %divide.args61, i64 0
  store %scriptum.value %str58, %scriptum.value* %divide.arg.slot62
  %divide.method63 = call %scriptum.value @scriptum_rt_text_divide(%scriptum.text* %text.ptr60, %scriptum.value* %divide.args61, i64 1)
  store %scriptum.value %divide.method63, %scriptum.value* %partes.slot51
  %unido.slot64 = alloca %scriptum.value
  %null65 = call %scriptum.value @scriptum_value_null()
  %text.data66 = getelementptr inbounds [3 x i8], [3 x i8]* @.str.2, i32 0, i32 0
  %text.new67 = call %scriptum.text* @scriptum_text_new(i8* %text.data66, i64 2)
  %str68 = call %scriptum.value @scriptum_value_text(%scriptum.text* %text.new67)
  %load69 = load %scriptum.value, %scriptum.value* %partes.slot51
  %spill70 = alloca %scriptum.value
  store %scriptum.value %str68, %scriptum.value* %spill70
  %text.ptr71 = call %scriptum.text* @scriptum_value_expect_text(%scriptum.value* %spill70)
  %coniunge.args72 = alloca %scriptum.value, i64 1
  %coniunge.arg.slot73 = getelementptr inbounds %scriptum.value, %scriptum.value* %coniunge.args72, i64 0
  store %scriptum.value %load69, %scriptum.value* %coniunge.arg.slot73
  %coniunge.method74 = call %scriptum.value @scriptum_rt_text_coniunge(%scriptum.text* %text.ptr71, %scriptum.value* %coniunge.args72, i64 1)
  store %scriptum.value %coniunge.method74, %scriptum.value* %unido.slot64
  %mutatus.slot75 = alloca %scriptum.value
  %null76 = call %scriptum.value @scriptum_value_null()
  %load77 = load %scriptum.value, %scriptum.value* %unido.slot64
  %text.data78 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.3, i32 0, i32 0
  %text.new79 = call %scriptum.text* @scriptum_text_new(i8* %text.data78, i64 1)
  %str80 = call %scriptum.value @scriptum_value_text(%scriptum.text* %text.new79)
  %text.data81 = getelementptr inbounds [2 x i8], [2 x i8]* @.str.4, i32 0, i32 0
  %text.new82 = call %scriptum.text* @scriptum_text_new(i8* %text.data81, i64 1)
  %str83 = call %scriptum.value @scriptum_value_text(%scriptum.text* %text.new82)
  %spill84 = alloca %scriptum.value
  store %scriptum.value %load77, %scriptum.value* %spill84
  %text.ptr85 = call %scriptum.text* @scriptum_value_expect_text(%scriptum.value* %spill84)
  %substitue.args86 = alloca %scriptum.value, i64 2
  %substitue.arg.slot87 = getelementptr inbounds %scriptum.value, %scriptum.value* %substitue.args86, i64 0
  store %scriptum.value %str80, %scriptum.value* %substitue.arg.slot87
  %substitue.arg.slot88 = getelementptr inbounds %scriptum.value, %scriptum.value* %substitue.args86, i64 1
  store %scriptum.value %str83, %scriptum.value* %substitue.arg.slot88
  %substitue.method89 = call %scriptum.value @scriptum_rt_text_substitue(%scriptum.text* %text.ptr85, %scriptum.value* %substitue.args86, i64 2)
  store %scriptum.value %substitue.method89, %scriptum.value* %mutatus.slot75
  %formatado.slot90 = alloca %scriptum.value
  %null91 = call %scriptum.value @scriptum_value_null()
  %load92 = load %scriptum.value, %scriptum.value* %mutatus.slot75
  %spill93 = alloca %scriptum.value
  store %scriptum.value %load92, %scriptum.value* %spill93
  %text.ptr94 = call %scriptum.text* @scriptum_value_expect_text(%scriptum.value* %spill93)
  %ad_maiusculas.method95 = call %scriptum.value @scriptum_rt_text_ad_maiusculas(%scriptum.text* %text.ptr94, %scriptum.value* null, i64 0)
  %spill96 = alloca %scriptum.value
  store %scriptum.value %ad_maiusculas.method95, %scriptum.value* %spill96
  %text.ptr97 = call %scriptum.text* @scriptum_value_expect_text(%scriptum.value* %spill96)
  %abscinde.method98 = call %scriptum.value @scriptum_rt_text_abscinde(%scriptum.text* %text.ptr97, %scriptum.value* null, i64 0)
  store %scriptum.value %abscinde.method98, %scriptum.value* %formatado.slot90
  %null99 = call %scriptum.value @scriptum_value_null()
  %load100 = load %scriptum.value, %scriptum.value* %partes.slot51
  %longitudo.args101 = alloca %scriptum.value, i64 1
  %longitudo.arg.slot102 = getelementptr inbounds %scriptum.value, %scriptum.value* %longitudo.args101, i64 0
  store %scriptum.value %load100, %scriptum.value* %longitudo.arg.slot102
  %longitudo.builtin103 = call %scriptum.value @scriptum_rt_longitudo(%scriptum.value* %longitudo.args101, i64 1)
  %spill104 = alloca %scriptum.value
  store %scriptum.value %longitudo.builtin103, %scriptum.value* %spill104
  %tonum105 = call double @scriptum_value_as_number(%scriptum.value* %spill104)
  %load106 = load %scriptum.value, %scriptum.value* %formatado.slot90
  %longitudo.args107 = alloca %scriptum.value, i64 1
  %longitudo.arg.slot108 = getelementptr inbounds %scriptum.value, %scriptum.value* %longitudo.args107, i64 0
  store %scriptum.value %load106, %scriptum.value* %longitudo.arg.slot108
  %longitudo.builtin109 = call %scriptum.value @scriptum_rt_longitudo(%scriptum.value* %longitudo.args107, i64 1)
  %spill110 = alloca %scriptum.value
  store %scriptum.value %longitudo.builtin109, %scriptum.value* %spill110
  %tonum111 = call double @scriptum_value_as_number(%scriptum.value* %spill110)
  %arith112 = fadd double %tonum105, %tonum111
  %fromnum113 = call %scriptum.value @scriptum_value_number(double %arith112)
  ret %scriptum.value %fromnum113
}
