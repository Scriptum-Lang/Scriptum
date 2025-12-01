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
@contador = internal global %scriptum.value { i32 1, double 0.000000, i32 0, i32 0, i8* null }
define %scriptum.value @atualizar(%scriptum.value %limite) {
entry:
  %limite.slot1 = alloca %scriptum.value
  store %scriptum.value %limite, %scriptum.value* %limite.slot1
  %total.slot2 = alloca %scriptum.value
  %num3 = call %scriptum.value @scriptum_value_number(double 0.0)
  %num4 = call %scriptum.value @scriptum_value_number(double 0.0)
  store %scriptum.value %num4, %scriptum.value* %total.slot2
  br label %while.cond5
while.cond5:
  %load8 = load %scriptum.value, %scriptum.value* %total.slot2
  %spill9 = alloca %scriptum.value
  store %scriptum.value %load8, %scriptum.value* %spill9
  %tonum10 = call double @scriptum_value_as_number(%scriptum.value* %spill9)
  %load11 = load %scriptum.value, %scriptum.value* %limite.slot1
  %spill12 = alloca %scriptum.value
  store %scriptum.value %load11, %scriptum.value* %spill12
  %tonum13 = call double @scriptum_value_as_number(%scriptum.value* %spill12)
  %cmp14 = fcmp olt double %tonum10, %tonum13
  %boolz15 = zext i1 %cmp14 to i32
  %boolwrap16 = call %scriptum.value @scriptum_value_boolean(i32 %boolz15)
  %spill17 = alloca %scriptum.value
  store %scriptum.value %boolwrap16, %scriptum.value* %spill17
  %bool3218 = call i32 @scriptum_value_as_boolean(%scriptum.value* %spill17)
  %bool19 = icmp ne i32 %bool3218, 0
  br i1 %bool19, label %while.body6, label %while.end7
while.body6:
  %load20 = load %scriptum.value, %scriptum.value* %total.slot2
  %spill21 = alloca %scriptum.value
  store %scriptum.value %load20, %scriptum.value* %spill21
  %tonum22 = call double @scriptum_value_as_number(%scriptum.value* %spill21)
  %num23 = call %scriptum.value @scriptum_value_number(double 1.0)
  %spill24 = alloca %scriptum.value
  store %scriptum.value %num23, %scriptum.value* %spill24
  %tonum25 = call double @scriptum_value_as_number(%scriptum.value* %spill24)
  %arith26 = fadd double %tonum22, %tonum25
  %fromnum27 = call %scriptum.value @scriptum_value_number(double %arith26)
  store %scriptum.value %fromnum27, %scriptum.value* %total.slot2
  %load28 = load %scriptum.value, %scriptum.value* %total.slot2
  %spill29 = alloca %scriptum.value
  store %scriptum.value %load28, %scriptum.value* %spill29
  %tonum30 = call double @scriptum_value_as_number(%scriptum.value* %spill29)
  %load31 = load %scriptum.value, %scriptum.value* %limite.slot1
  %spill32 = alloca %scriptum.value
  store %scriptum.value %load31, %scriptum.value* %spill32
  %tonum33 = call double @scriptum_value_as_number(%scriptum.value* %spill32)
  %cmp34 = fcmp oeq double %tonum30, %tonum33
  %boolz35 = zext i1 %cmp34 to i32
  %boolwrap36 = call %scriptum.value @scriptum_value_boolean(i32 %boolz35)
  %spill37 = alloca %scriptum.value
  store %scriptum.value %boolwrap36, %scriptum.value* %spill37
  %bool3238 = call i32 @scriptum_value_as_boolean(%scriptum.value* %spill37)
  %bool39 = icmp ne i32 %bool3238, 0
  br i1 %bool39, label %if.then40, label %if.else41
  br label %while.cond5
if.then40:
  br label %while.end7
if.else41:
  br label %while.cond5
if.end42:
while.end7:
  %null43 = call %scriptum.value @scriptum_value_null()
  %load44 = load %scriptum.value, %scriptum.value* %total.slot2
  %kind45 = extractvalue %scriptum.value %load44, 0
  %kindcmp46 = icmp eq i32 %kind45, 8
  br i1 %kindcmp46, label %nullish.rhs47, label %nullish.end48
nullish.rhs47:
  %num49 = call %scriptum.value @scriptum_value_number(double 0.0)
  br label %nullish.end48
nullish.end48:
  %nullish50 = phi %scriptum.value [ %load44, %while.end7 ], [ %num49, %nullish.rhs47 ]
  ret %scriptum.value %nullish50
}
