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
define %scriptum.value @principalis() {
entry:
  %total.slot1 = alloca %scriptum.value
  %num2 = call %scriptum.value @scriptum_value_number(double 0.0)
  %num3 = call %scriptum.value @scriptum_value_number(double 0.0)
  store %scriptum.value %num3, %scriptum.value* %total.slot1
  %collection.slot4 = alloca %scriptum.value
  %null5 = call %scriptum.value @scriptum_value_null()
  %array.new6 = call %scriptum.array* @scriptum_array_new(i64 3)
  %num7 = call %scriptum.value @scriptum_value_number(double 1.0)
  call void @scriptum_array_push(%scriptum.array* %array.new6, %scriptum.value %num7)
  %num8 = call %scriptum.value @scriptum_value_number(double 2.0)
  call void @scriptum_array_push(%scriptum.array* %array.new6, %scriptum.value %num8)
  %num9 = call %scriptum.value @scriptum_value_number(double 3.0)
  call void @scriptum_array_push(%scriptum.array* %array.new6, %scriptum.value %num9)
  %array.wrap10 = call %scriptum.value @scriptum_value_array(%scriptum.array* %array.new6)
  store %scriptum.value %array.wrap10, %scriptum.value* %collection.slot4
  %load11 = load %scriptum.value, %scriptum.value* %collection.slot4
  %spill12 = alloca %scriptum.value
  store %scriptum.value %load11, %scriptum.value* %spill12
  %array.ptr13 = call %scriptum.array* @scriptum_value_expect_array(%scriptum.value* %spill12)
  %for.len14 = call i64 @scriptum_array_len(%scriptum.array* %array.ptr13)
  %for.index.slot15 = alloca i64
  store i64 0, i64* %for.index.slot15
  br label %for.cond16
for.cond16:
  %for.idx19 = load i64, i64* %for.index.slot15
  %for.cmp20 = icmp slt i64 %for.idx19, %for.len14
  br i1 %for.cmp20, label %for.body17, label %for.end18
for.body17:
  %valor.slot21 = alloca %scriptum.value
  %valor.current.slot22 = alloca %scriptum.value
  %for.body.idx23 = load i64, i64* %for.index.slot15
  call i32 @scriptum_array_get(%scriptum.array* %array.ptr13, i64 %for.body.idx23, %scriptum.value* %valor.current.slot22)
  %load24 = load %scriptum.value, %scriptum.value* %valor.current.slot22
  store %scriptum.value %load24, %scriptum.value* %valor.slot21
  %load25 = load %scriptum.value, %scriptum.value* %total.slot1
  %spill26 = alloca %scriptum.value
  store %scriptum.value %load25, %scriptum.value* %spill26
  %tonum27 = call double @scriptum_value_as_number(%scriptum.value* %spill26)
  %load28 = load %scriptum.value, %scriptum.value* %valor.slot21
  %spill29 = alloca %scriptum.value
  store %scriptum.value %load28, %scriptum.value* %spill29
  %tonum30 = call double @scriptum_value_as_number(%scriptum.value* %spill29)
  %arith31 = fadd double %tonum27, %tonum30
  %fromnum32 = call %scriptum.value @scriptum_value_number(double %arith31)
  store %scriptum.value %fromnum32, %scriptum.value* %total.slot1
  %for.next33 = add i64 %for.body.idx23, 1
  store i64 %for.next33, i64* %for.index.slot15
  br label %for.cond16
for.end18:
  %null34 = call %scriptum.value @scriptum_value_null()
  %load35 = load %scriptum.value, %scriptum.value* %total.slot1
  ret %scriptum.value %load35
}
