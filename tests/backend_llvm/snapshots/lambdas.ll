; ModuleID = "scriptum"
source_filename = "scriptum"
%lambda.capture.0 = type { %scriptum.value }
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
define %scriptum.value @lambda.0.entry(i8* %lambda.closure.raw, %scriptum.value* %lambda.args.raw, i64 %lambda.argc) {
entry:
  %lambda.closure.ptr9 = bitcast i8* %lambda.closure.raw to %lambda.capture.0*
  %lambda.capture.ptr10 = getelementptr inbounds %lambda.capture.0, %lambda.capture.0* %lambda.closure.ptr9, i32 0, i32 0
  %lambda.capture.load11 = load %scriptum.value, %scriptum.value* %lambda.capture.ptr10
  %base.slot12 = alloca %scriptum.value
  store %scriptum.value %lambda.capture.load11, %scriptum.value* %base.slot12
  %x.slot13 = alloca %scriptum.value
  %lambda.arg.cmp14 = icmp ugt i64 %lambda.argc, 0
  br i1 %lambda.arg.cmp14, label %lambda.arg0.value15, label %lambda.arg0.default16
lambda.arg0.value15:
  %lambda.arg.ptr18 = getelementptr inbounds %scriptum.value, %scriptum.value* %lambda.args.raw, i64 0
  %lambda.arg.load19 = load %scriptum.value, %scriptum.value* %lambda.arg.ptr18
  br label %lambda.arg0.merge17
lambda.arg0.default16:
  %null20 = call %scriptum.value @scriptum_value_null()
  br label %lambda.arg0.merge17
lambda.arg0.merge17:
  %lambda.arg.phi21 = phi %scriptum.value [ %lambda.arg.load19, %lambda.arg0.value15 ], [ %null20, %lambda.arg0.default16 ]
  store %scriptum.value %lambda.arg.phi21, %scriptum.value* %x.slot13
  %null22 = call %scriptum.value @scriptum_value_null()
  %load23 = load %scriptum.value, %scriptum.value* %x.slot13
  %spill24 = alloca %scriptum.value
  store %scriptum.value %load23, %scriptum.value* %spill24
  %tonum25 = call double @scriptum_value_as_number(%scriptum.value* %spill24)
  %load26 = load %scriptum.value, %scriptum.value* %base.slot12
  %spill27 = alloca %scriptum.value
  store %scriptum.value %load26, %scriptum.value* %spill27
  %tonum28 = call double @scriptum_value_as_number(%scriptum.value* %spill27)
  %arith29 = fadd double %tonum25, %tonum28
  %fromnum30 = call %scriptum.value @scriptum_value_number(double %arith29)
  ret %scriptum.value %fromnum30
}
define %scriptum.value @principalis() {
entry:
  %base.slot1 = alloca %scriptum.value
  %num2 = call %scriptum.value @scriptum_value_number(double 0.0)
  %num3 = call %scriptum.value @scriptum_value_number(double 5.0)
  store %scriptum.value %num3, %scriptum.value* %base.slot1
  %offset.slot4 = alloca %scriptum.value
  %num5 = call %scriptum.value @scriptum_value_number(double 0.0)
  %num6 = call %scriptum.value @scriptum_value_number(double 2.0)
  store %scriptum.value %num6, %scriptum.value* %offset.slot4
  %mapper.slot7 = alloca %scriptum.value
  %null8 = call %scriptum.value @scriptum_value_null()
  %lambda.cap.size.ptr31 = getelementptr inbounds %lambda.capture.0, %lambda.capture.0* null, i32 1
  %lambda.cap.size32 = ptrtoint %lambda.capture.0* %lambda.cap.size.ptr31 to i64
  %lambda.cap.raw33 = call i8* @scriptum_alloc(i64 %lambda.cap.size32)
  %lambda.cap.ptr34 = bitcast i8* %lambda.cap.raw33 to %lambda.capture.0*
  %lambda.cap.field35 = getelementptr inbounds %lambda.capture.0, %lambda.capture.0* %lambda.cap.ptr34, i32 0, i32 0
  %load36 = load %scriptum.value, %scriptum.value* %base.slot1
  store %scriptum.value %load36, %scriptum.value* %lambda.cap.field35
  %lambda.new37 = call %scriptum.lambda* @scriptum_lambda_new(%scriptum.value (i8*, %scriptum.value*, i64)* @lambda.0.entry, i8* %lambda.cap.raw33)
  %lambda.wrap38 = call %scriptum.value @scriptum_value_lambda(%scriptum.lambda* %lambda.new37)
  store %scriptum.value %lambda.wrap38, %scriptum.value* %mapper.slot7
  %load39 = load %scriptum.value, %scriptum.value* %base.slot1
  %spill40 = alloca %scriptum.value
  store %scriptum.value %load39, %scriptum.value* %spill40
  %tonum41 = call double @scriptum_value_as_number(%scriptum.value* %spill40)
  %load42 = load %scriptum.value, %scriptum.value* %offset.slot4
  %spill43 = alloca %scriptum.value
  store %scriptum.value %load42, %scriptum.value* %spill43
  %tonum44 = call double @scriptum_value_as_number(%scriptum.value* %spill43)
  %arith45 = fadd double %tonum41, %tonum44
  %fromnum46 = call %scriptum.value @scriptum_value_number(double %arith45)
  store %scriptum.value %fromnum46, %scriptum.value* %base.slot1
  %null47 = call %scriptum.value @scriptum_value_null()
  %load48 = load %scriptum.value, %scriptum.value* %mapper.slot7
  %num49 = call %scriptum.value @scriptum_value_number(double 3.0)
  %spill50 = alloca %scriptum.value
  store %scriptum.value %load48, %scriptum.value* %spill50
  %lambda.ptr51 = call %scriptum.lambda* @scriptum_value_expect_lambda(%scriptum.value* %spill50)
  %lambda.args52 = alloca %scriptum.value, i64 1
  %lambda.arg.slot53 = getelementptr inbounds %scriptum.value, %scriptum.value* %lambda.args52, i64 0
  store %scriptum.value %num49, %scriptum.value* %lambda.arg.slot53
  %lambda.call54 = call %scriptum.value @scriptum_lambda_call(%scriptum.lambda* %lambda.ptr51, %scriptum.value* %lambda.args52, i64 1)
  ret %scriptum.value %lambda.call54
}
