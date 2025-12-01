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
  %numbers.slot1 = alloca %scriptum.value
  %null2 = call %scriptum.value @scriptum_value_null()
  %array.new3 = call %scriptum.array* @scriptum_array_new(i64 3)
  %num4 = call %scriptum.value @scriptum_value_number(double 10.0)
  call void @scriptum_array_push(%scriptum.array* %array.new3, %scriptum.value %num4)
  %num5 = call %scriptum.value @scriptum_value_number(double 20.0)
  call void @scriptum_array_push(%scriptum.array* %array.new3, %scriptum.value %num5)
  %num6 = call %scriptum.value @scriptum_value_number(double 30.0)
  call void @scriptum_array_push(%scriptum.array* %array.new3, %scriptum.value %num6)
  %array.wrap7 = call %scriptum.value @scriptum_value_array(%scriptum.array* %array.new3)
  store %scriptum.value %array.wrap7, %scriptum.value* %numbers.slot1
  %total.slot8 = alloca %scriptum.value
  %num9 = call %scriptum.value @scriptum_value_number(double 0.0)
  %load10 = load %scriptum.value, %scriptum.value* %numbers.slot1
  %summa.args11 = alloca %scriptum.value, i64 1
  %summa.arg.slot12 = getelementptr inbounds %scriptum.value, %scriptum.value* %summa.args11, i64 0
  store %scriptum.value %load10, %scriptum.value* %summa.arg.slot12
  %summa.builtin13 = call %scriptum.value @scriptum_rt_summa(%scriptum.value* %summa.args11, i64 1)
  store %scriptum.value %summa.builtin13, %scriptum.value* %total.slot8
  %null14 = call %scriptum.value @scriptum_value_null()
  %load15 = load %scriptum.value, %scriptum.value* %total.slot8
  ret %scriptum.value %load15
}
