#ifndef SCRIPTUM_RUNTIME_H
#define SCRIPTUM_RUNTIME_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum scriptum_value_kind {
    SCRIPTUM_VALUE_UNDEFINED = 0,
    SCRIPTUM_VALUE_NUMBER,
    SCRIPTUM_VALUE_BOOLEAN,
    SCRIPTUM_VALUE_TEXT,
    SCRIPTUM_VALUE_ARRAY,
    SCRIPTUM_VALUE_OBJECT,
    SCRIPTUM_VALUE_LAMBDA,
    SCRIPTUM_VALUE_OPTIONAL,
    SCRIPTUM_VALUE_NULL
} scriptum_value_kind;

typedef struct scriptum_value scriptum_value;

struct scriptum_value {
    scriptum_value_kind kind;
    double number;
    int32_t boolean;
    uint32_t _reserved;
    void *payload;
};

typedef struct scriptum_text {
    uint64_t ref_count;
    uint64_t length;
    char *data;
} scriptum_text;

typedef struct scriptum_array {
    uint64_t ref_count;
    uint64_t length;
    uint64_t capacity;
    scriptum_value *items;
} scriptum_array;

typedef struct scriptum_object_entry {
    scriptum_text *key;
    scriptum_value value;
} scriptum_object_entry;

typedef struct scriptum_object {
    uint64_t ref_count;
    uint64_t length;
    uint64_t capacity;
    scriptum_object_entry *entries;
} scriptum_object;

typedef struct scriptum_lambda scriptum_lambda;
typedef scriptum_value (*scriptum_lambda_entry)(void *closure, scriptum_value *args, uint64_t argc);

struct scriptum_lambda {
    uint64_t ref_count;
    scriptum_lambda_entry entry;
    void *closure;
};

typedef struct scriptum_optional {
    uint64_t ref_count;
    uint8_t is_present;
    uint8_t _padding[7];
    scriptum_value value;
} scriptum_optional;

/* Allocation helpers */
void *scriptum_alloc(uint64_t size);
void scriptum_release(void *ptr);

/* Reference counting for heap-backed payloads */
void scriptum_text_retain(scriptum_text *text);
void scriptum_text_release(scriptum_text *text);

void scriptum_array_retain(scriptum_array *array);
void scriptum_array_release(scriptum_array *array);

void scriptum_object_retain(scriptum_object *object);
void scriptum_object_release(scriptum_object *object);

void scriptum_lambda_retain(scriptum_lambda *lambda);
void scriptum_lambda_release(scriptum_lambda *lambda);

void scriptum_optional_retain(scriptum_optional *optional);
void scriptum_optional_release(scriptum_optional *optional);

/* Value constructors */
scriptum_value scriptum_value_number(double number);
scriptum_value scriptum_value_boolean(int32_t flag);
scriptum_value scriptum_value_null(void);
scriptum_value scriptum_value_text(scriptum_text *text);
scriptum_value scriptum_value_array(scriptum_array *array);
scriptum_value scriptum_value_object(scriptum_object *object);
scriptum_value scriptum_value_lambda(scriptum_lambda *lambda);
scriptum_value scriptum_value_optional(scriptum_optional *optional);

/* Result helpers */
void scriptum_rt_dump(scriptum_value value);

/* Value conversions */
double scriptum_value_as_number(const scriptum_value *value);
int32_t scriptum_value_as_boolean(const scriptum_value *value);
scriptum_text *scriptum_value_expect_text(const scriptum_value *value);
scriptum_array *scriptum_value_expect_array(const scriptum_value *value);
scriptum_object *scriptum_value_expect_object(const scriptum_value *value);
scriptum_lambda *scriptum_value_expect_lambda(const scriptum_value *value);
scriptum_optional *scriptum_value_expect_optional(const scriptum_value *value);

/* Text helpers */
scriptum_text *scriptum_text_new(const char *data, uint64_t length);
scriptum_text *scriptum_text_concat(scriptum_text *lhs, scriptum_text *rhs);
int32_t scriptum_text_compare(scriptum_text *lhs, scriptum_text *rhs);

/* Array helpers */
scriptum_array *scriptum_array_new(uint64_t capacity);
void scriptum_array_push(scriptum_array *array, scriptum_value value);
int scriptum_array_get(scriptum_array *array, uint64_t index, scriptum_value *out);
int scriptum_array_set(scriptum_array *array, uint64_t index, scriptum_value value);
uint64_t scriptum_array_len(const scriptum_array *array);

/* Object helpers */
scriptum_object *scriptum_object_new(void);
void scriptum_object_set(scriptum_object *object, scriptum_text *key, scriptum_value value);
int scriptum_object_get(scriptum_object *object, scriptum_text *key, scriptum_value *out);

/* Optional helpers */
scriptum_optional *scriptum_optional_new(scriptum_value value);
scriptum_value scriptum_optional_or_else(scriptum_optional *optional, scriptum_value fallback);

/* Lambda helpers */
scriptum_lambda *scriptum_lambda_new(scriptum_lambda_entry entry, void *closure);
scriptum_value scriptum_lambda_call(scriptum_lambda *lambda, scriptum_value *args, uint64_t argc);

/* Builtin runtime helpers */
scriptum_value scriptum_rt_scribe(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_longitudo(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_numerus(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_textus(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_booleanum(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_ambitus(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_summa(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_minimum(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_maximum(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_absolutum(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_aliquod(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_omnia(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_lege(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_enumera(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_coniunge(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_applica(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_filtra(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_ordina(scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_array_adde(scriptum_array *array, scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_array_exime(scriptum_array *array, scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_array_extende(scriptum_array *array, scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_array_inserta(scriptum_array *array, scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_array_remove(scriptum_array *array, scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_array_purga(scriptum_array *array, scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_text_divide(scriptum_text *text, scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_text_coniunge(scriptum_text *text, scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_text_substitue(scriptum_text *text, scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_text_ad_minusculas(scriptum_text *text, scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_text_ad_maiusculas(scriptum_text *text, scriptum_value *args, uint64_t argc);
scriptum_value scriptum_rt_text_abscinde(scriptum_text *text, scriptum_value *args, uint64_t argc);

#ifdef __cplusplus
}
#endif

#endif /* SCRIPTUM_RUNTIME_H */
