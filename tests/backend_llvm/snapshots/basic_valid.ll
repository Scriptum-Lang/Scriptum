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
@base = internal global %scriptum.value { i32 1, double 1.000000, i32 1, i32 0, i8* null }
define %scriptum.value @principalis() {
entry:
  %total.slot1 = alloca %scriptum.value
  %num2 = call %scriptum.value @scriptum_value_number(double 0.0)
  %gload3 = load %scriptum.value, %scriptum.value* @base
  %spill4 = alloca %scriptum.value
  store %scriptum.value %gload3, %scriptum.value* %spill4
  %tonum5 = call double @scriptum_value_as_number(%scriptum.value* %spill4)
  %num6 = call %scriptum.value @scriptum_value_number(double 2.0)
  %spill7 = alloca %scriptum.value
  store %scriptum.value %num6, %scriptum.value* %spill7
  %tonum8 = call double @scriptum_value_as_number(%scriptum.value* %spill7)
  %arith9 = fadd double %tonum5, %tonum8
  %fromnum10 = call %scriptum.value @scriptum_value_number(double %arith9)
  store %scriptum.value %fromnum10, %scriptum.value* %total.slot1
  %null11 = call %scriptum.value @scriptum_value_null()
  %load12 = load %scriptum.value, %scriptum.value* %total.slot1
  ret %scriptum.value %load12
}
