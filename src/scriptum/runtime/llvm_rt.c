#include "runtime.h"

#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static scriptum_value scriptum_value_clone(const scriptum_value *value);
static void scriptum_value_dispose(scriptum_value *value);
static void scriptum_rt_dump_array(FILE *stream, scriptum_array *array);
static void scriptum_rt_dump_object(FILE *stream, scriptum_object *object);
static void scriptum_rt_dump_text(FILE *stream, scriptum_text *text);
static void scriptum_rt_dump_value(FILE *stream, scriptum_value value);

typedef struct scriptum_string_builder {
    char *data;
    uint64_t length;
    uint64_t capacity;
} scriptum_string_builder;

typedef struct scriptum_sort_entry {
    scriptum_value value;
    scriptum_text *key_text;
} scriptum_sort_entry;

static void scriptum_sb_init(scriptum_string_builder *builder);
static void scriptum_sb_reset(scriptum_string_builder *builder);
static int scriptum_sb_reserve(scriptum_string_builder *builder, uint64_t capacity);
static void scriptum_sb_append_char(scriptum_string_builder *builder, char ch);
static void scriptum_sb_append_bytes(scriptum_string_builder *builder, const char *data, uint64_t length);
static void scriptum_sb_append_cstr(scriptum_string_builder *builder, const char *text);
static void scriptum_rt_format_value(scriptum_string_builder *builder, const scriptum_value *value);
static int scriptum_rt_truthy(const scriptum_value *value);
static int scriptum_rt_parse_number(const scriptum_value *value, double *out_number);
static int scriptum_rt_parse_integer(const scriptum_value *value, int64_t *out_value);
static scriptum_text *scriptum_rt_text_from_value(const scriptum_value *value);
static scriptum_text *scriptum_rt_read_input_line(void);
static scriptum_value scriptum_rt_arg(scriptum_value *args, uint64_t argc, uint64_t index);
static void scriptum_rt_sort_entries(scriptum_sort_entry *entries, uint64_t length, int reverse);
static scriptum_text *scriptum_rt_text_slice(scriptum_text *text, uint64_t start, uint64_t length);
static uint64_t scriptum_rt_text_find(scriptum_text *text, scriptum_text *pattern, uint64_t start);
static int scriptum_rt_values_equal(const scriptum_value *lhs, const scriptum_value *rhs);

void *scriptum_alloc(uint64_t size) {
    if (size == 0) {
        size = 1;
    }
    void *ptr = calloc(1, (size_t)size);
    return ptr;
}

void scriptum_release(void *ptr) {
    free(ptr);
}

static scriptum_text *scriptum_text_alloc(uint64_t length) {
    scriptum_text *text = (scriptum_text *)scriptum_alloc(sizeof(scriptum_text));
    if (text == NULL) {
        return NULL;
    }
    text->ref_count = 1;
    text->length = length;
    if (length == 0) {
        text->data = NULL;
        return text;
    }
    text->data = (char *)scriptum_alloc(length + 1);
    if (text->data == NULL) {
        scriptum_release(text);
        return NULL;
    }
    text->data[length] = '\0';
    return text;
}

scriptum_text *scriptum_text_new(const char *data, uint64_t length) {
    scriptum_text *text = scriptum_text_alloc(length);
    if (text == NULL) {
        return NULL;
    }
    if (length > 0 && data != NULL) {
        memcpy(text->data, data, (size_t)length);
        text->data[length] = '\0';
    }
    return text;
}

void scriptum_text_retain(scriptum_text *text) {
    if (text != NULL) {
        text->ref_count++;
    }
}

void scriptum_text_release(scriptum_text *text) {
    if (text == NULL) {
        return;
    }
    if (text->ref_count > 0) {
        text->ref_count--;
    }
    if (text->ref_count == 0) {
        if (text->data) {
            scriptum_release(text->data);
        }
        scriptum_release(text);
    }
}

scriptum_text *scriptum_text_concat(scriptum_text *lhs, scriptum_text *rhs) {
    uint64_t left_len = lhs ? lhs->length : 0;
    uint64_t right_len = rhs ? rhs->length : 0;
    scriptum_text *text = scriptum_text_alloc(left_len + right_len);
    if (text == NULL) {
        return NULL;
    }
    if (lhs && lhs->data) {
        memcpy(text->data, lhs->data, (size_t)left_len);
    }
    if (rhs && rhs->data) {
        memcpy(text->data + left_len, rhs->data, (size_t)right_len);
    }
    text->data[text->length] = '\0';
    return text;
}

int32_t scriptum_text_compare(scriptum_text *lhs, scriptum_text *rhs) {
    if (lhs == rhs) {
        return 0;
    }
    if (lhs == NULL) {
        return rhs == NULL ? 0 : -1;
    }
    if (rhs == NULL) {
        return 1;
    }
    if (lhs->length != rhs->length) {
        return (lhs->length < rhs->length) ? -1 : 1;
    }
    if (lhs->length == 0) {
        return 0;
    }
    int cmp = memcmp(lhs->data, rhs->data, (size_t)lhs->length);
    if (cmp == 0) {
        return 0;
    }
    return cmp < 0 ? -1 : 1;
}

scriptum_array *scriptum_array_new(uint64_t capacity) {
    scriptum_array *array = (scriptum_array *)scriptum_alloc(sizeof(scriptum_array));
    if (array == NULL) {
        return NULL;
    }
    if (capacity == 0) {
        capacity = 4;
    }
    array->ref_count = 1;
    array->length = 0;
    array->capacity = capacity;
    array->items = (scriptum_value *)scriptum_alloc(sizeof(scriptum_value) * capacity);
    if (array->items == NULL) {
        scriptum_release(array);
        return NULL;
    }
    return array;
}

void scriptum_array_retain(scriptum_array *array) {
    if (array != NULL) {
        array->ref_count++;
    }
}

static void scriptum_array_dispose(scriptum_array *array) {
    if (array == NULL) {
        return;
    }
    if (array->items != NULL) {
        for (uint64_t i = 0; i < array->length; ++i) {
            scriptum_value_dispose(&array->items[i]);
        }
        scriptum_release(array->items);
    }
    scriptum_release(array);
}

void scriptum_array_release(scriptum_array *array) {
    if (array == NULL) {
        return;
    }
    if (array->ref_count > 0) {
        array->ref_count--;
    }
    if (array->ref_count == 0) {
        scriptum_array_dispose(array);
    }
}

static int scriptum_array_reserve(scriptum_array *array, uint64_t new_capacity) {
    if (new_capacity <= array->capacity) {
        return 1;
    }
    scriptum_value *items = (scriptum_value *)realloc(array->items, sizeof(scriptum_value) * new_capacity);
    if (items == NULL) {
        return 0;
    }
    array->items = items;
    array->capacity = new_capacity;
    return 1;
}

void scriptum_array_push(scriptum_array *array, scriptum_value value) {
    if (array == NULL) {
        return;
    }
    if (array->length == array->capacity) {
        uint64_t next_capacity = array->capacity ? array->capacity * 2 : 4;
        if (!scriptum_array_reserve(array, next_capacity)) {
            return;
        }
    }
    array->items[array->length++] = scriptum_value_clone(&value);
}

int scriptum_array_get(scriptum_array *array, uint64_t index, scriptum_value *out) {
    if (array == NULL || out == NULL) {
        return 0;
    }
    if (index >= array->length) {
        return 0;
    }
    *out = scriptum_value_clone(&array->items[index]);
    return 1;
}

int scriptum_array_set(scriptum_array *array, uint64_t index, scriptum_value value) {
    if (array == NULL) {
        return 0;
    }
    if (index >= array->length) {
        return 0;
    }
    scriptum_value_dispose(&array->items[index]);
    array->items[index] = scriptum_value_clone(&value);
    return 1;
}

uint64_t scriptum_array_len(const scriptum_array *array) {
    return array ? array->length : 0;
}

scriptum_object *scriptum_object_new(void) {
    scriptum_object *object = (scriptum_object *)scriptum_alloc(sizeof(scriptum_object));
    if (object == NULL) {
        return NULL;
    }
    object->ref_count = 1;
    object->length = 0;
    object->capacity = 4;
    object->entries = (scriptum_object_entry *)scriptum_alloc(sizeof(scriptum_object_entry) * object->capacity);
    if (object->entries == NULL) {
        scriptum_release(object);
        return NULL;
    }
    return object;
}

void scriptum_object_retain(scriptum_object *object) {
    if (object != NULL) {
        object->ref_count++;
    }
}

static void scriptum_object_dispose(scriptum_object *object) {
    if (!object) {
        return;
    }
    if (object->entries) {
        for (uint64_t i = 0; i < object->length; ++i) {
            scriptum_object_entry *entry = &object->entries[i];
            if (entry->key) {
                scriptum_text_release(entry->key);
            }
            scriptum_value_dispose(&entry->value);
        }
        scriptum_release(object->entries);
    }
    scriptum_release(object);
}

void scriptum_object_release(scriptum_object *object) {
    if (object == NULL) {
        return;
    }
    if (object->ref_count > 0) {
        object->ref_count--;
    }
    if (object->ref_count == 0) {
        scriptum_object_dispose(object);
    }
}

static int scriptum_object_reserve(scriptum_object *object, uint64_t capacity) {
    if (capacity <= object->capacity) {
        return 1;
    }
    scriptum_object_entry *entries =
        (scriptum_object_entry *)realloc(object->entries, sizeof(scriptum_object_entry) * capacity);
    if (entries == NULL) {
        return 0;
    }
    object->entries = entries;
    object->capacity = capacity;
    return 1;
}

void scriptum_object_set(scriptum_object *object, scriptum_text *key, scriptum_value value) {
    if (object == NULL || key == NULL) {
        return;
    }
    for (uint64_t i = 0; i < object->length; ++i) {
        scriptum_object_entry *entry = &object->entries[i];
        if (scriptum_text_compare(entry->key, key) == 0) {
            scriptum_value_dispose(&entry->value);
            entry->value = scriptum_value_clone(&value);
            return;
        }
    }
    if (object->length == object->capacity) {
        uint64_t next = object->capacity ? object->capacity * 2 : 4;
        if (!scriptum_object_reserve(object, next)) {
            return;
        }
    }
    scriptum_object_entry *entry = &object->entries[object->length++];
    entry->key = key;
    scriptum_text_retain(key);
    entry->value = scriptum_value_clone(&value);
}

int scriptum_object_get(scriptum_object *object, scriptum_text *key, scriptum_value *out) {
    if (object == NULL || key == NULL || out == NULL) {
        return 0;
    }
    for (uint64_t i = 0; i < object->length; ++i) {
        scriptum_object_entry *entry = &object->entries[i];
        if (scriptum_text_compare(entry->key, key) == 0) {
            *out = scriptum_value_clone(&entry->value);
            return 1;
        }
    }
    return 0;
}

void scriptum_lambda_retain(scriptum_lambda *lambda) {
    if (lambda != NULL) {
        lambda->ref_count++;
    }
}

void scriptum_lambda_release(scriptum_lambda *lambda) {
    if (lambda == NULL) {
        return;
    }
    if (lambda->ref_count > 0) {
        lambda->ref_count--;
    }
    if (lambda->ref_count == 0) {
        scriptum_release(lambda);
    }
}

scriptum_lambda *scriptum_lambda_new(scriptum_lambda_entry entry, void *closure) {
    if (entry == NULL) {
        return NULL;
    }
    scriptum_lambda *lambda = (scriptum_lambda *)scriptum_alloc(sizeof(scriptum_lambda));
    if (lambda == NULL) {
        return NULL;
    }
    lambda->ref_count = 1;
    lambda->entry = entry;
    lambda->closure = closure;
    return lambda;
}

scriptum_value scriptum_lambda_call(scriptum_lambda *lambda, scriptum_value *args, uint64_t argc) {
    if (lambda == NULL || lambda->entry == NULL) {
        return scriptum_value_null();
    }
    return lambda->entry(lambda->closure, args, argc);
}

static scriptum_optional *scriptum_optional_alloc(void) {
    scriptum_optional *optional = (scriptum_optional *)scriptum_alloc(sizeof(scriptum_optional));
    if (optional != NULL) {
        optional->ref_count = 1;
        optional->is_present = 0;
    }
    return optional;
}

void scriptum_optional_retain(scriptum_optional *optional) {
    if (optional != NULL) {
        optional->ref_count++;
    }
}

void scriptum_optional_release(scriptum_optional *optional) {
    if (optional == NULL) {
        return;
    }
    if (optional->ref_count > 0) {
        optional->ref_count--;
    }
    if (optional->ref_count == 0) {
        if (optional->is_present) {
            scriptum_value_dispose(&optional->value);
        }
        scriptum_release(optional);
    }
}

scriptum_optional *scriptum_optional_new(scriptum_value value) {
    scriptum_optional *optional = scriptum_optional_alloc();
    if (optional == NULL) {
        return NULL;
    }
    optional->is_present = 1;
    optional->value = scriptum_value_clone(&value);
    return optional;
}

scriptum_value scriptum_optional_or_else(scriptum_optional *optional, scriptum_value fallback) {
    if (optional && optional->is_present) {
        return scriptum_value_clone(&optional->value);
    }
    return scriptum_value_clone(&fallback);
}

scriptum_value scriptum_value_number(double number) {
    scriptum_value value;
    value.kind = SCRIPTUM_VALUE_NUMBER;
    value.number = number;
    value.boolean = number != 0.0;
    value._reserved = 0;
    value.payload = NULL;
    return value;
}

scriptum_value scriptum_value_boolean(int32_t flag) {
    scriptum_value value;
    value.kind = SCRIPTUM_VALUE_BOOLEAN;
    value.number = flag ? 1.0 : 0.0;
    value.boolean = flag ? 1 : 0;
    value._reserved = 0;
    value.payload = NULL;
    return value;
}

scriptum_value scriptum_value_null(void) {
    scriptum_value value;
    value.kind = SCRIPTUM_VALUE_NULL;
    value.number = 0.0;
    value.boolean = 0;
    value._reserved = 0;
    value.payload = NULL;
    return value;
}

scriptum_value scriptum_value_text(scriptum_text *text) {
    scriptum_value value = scriptum_value_null();
    value.kind = SCRIPTUM_VALUE_TEXT;
    value.payload = text;
    return value;
}

scriptum_value scriptum_value_array(scriptum_array *array) {
    scriptum_value value = scriptum_value_null();
    value.kind = SCRIPTUM_VALUE_ARRAY;
    value.payload = array;
    return value;
}

scriptum_value scriptum_value_object(scriptum_object *object) {
    scriptum_value value = scriptum_value_null();
    value.kind = SCRIPTUM_VALUE_OBJECT;
    value.payload = object;
    return value;
}

scriptum_value scriptum_value_lambda(scriptum_lambda *lambda) {
    scriptum_value value = scriptum_value_null();
    value.kind = SCRIPTUM_VALUE_LAMBDA;
    value.payload = lambda;
    return value;
}

scriptum_value scriptum_value_optional(scriptum_optional *optional) {
    scriptum_value value = scriptum_value_null();
    value.kind = SCRIPTUM_VALUE_OPTIONAL;
    value.payload = optional;
    return value;
}

double scriptum_value_as_number(const scriptum_value *value) {
    if (value == NULL) {
        return 0.0;
    }
    switch (value->kind) {
        case SCRIPTUM_VALUE_NUMBER:
            return value->number;
        case SCRIPTUM_VALUE_BOOLEAN:
            return value->boolean ? 1.0 : 0.0;
        default:
            return 0.0;
    }
}

int32_t scriptum_value_as_boolean(const scriptum_value *value) {
    if (value == NULL) {
        return 0;
    }
    switch (value->kind) {
        case SCRIPTUM_VALUE_BOOLEAN:
            return value->boolean != 0;
        case SCRIPTUM_VALUE_NUMBER:
            return value->number != 0.0;
        case SCRIPTUM_VALUE_NULL:
            return 0;
        case SCRIPTUM_VALUE_TEXT:
        case SCRIPTUM_VALUE_ARRAY:
        case SCRIPTUM_VALUE_OBJECT:
        case SCRIPTUM_VALUE_LAMBDA:
            return value->payload != NULL;
        case SCRIPTUM_VALUE_OPTIONAL: {
            scriptum_optional *opt = (scriptum_optional *)value->payload;
            return opt && opt->is_present;
        }
        default:
            return 0;
    }
}

scriptum_text *scriptum_value_expect_text(const scriptum_value *value) {
    if (value && value->kind == SCRIPTUM_VALUE_TEXT) {
        return (scriptum_text *)value->payload;
    }
    return NULL;
}

scriptum_array *scriptum_value_expect_array(const scriptum_value *value) {
    if (value && value->kind == SCRIPTUM_VALUE_ARRAY) {
        return (scriptum_array *)value->payload;
    }
    return NULL;
}

scriptum_object *scriptum_value_expect_object(const scriptum_value *value) {
    if (value && value->kind == SCRIPTUM_VALUE_OBJECT) {
        return (scriptum_object *)value->payload;
    }
    return NULL;
}

scriptum_lambda *scriptum_value_expect_lambda(const scriptum_value *value) {
    if (value && value->kind == SCRIPTUM_VALUE_LAMBDA) {
        return (scriptum_lambda *)value->payload;
    }
    return NULL;
}

scriptum_optional *scriptum_value_expect_optional(const scriptum_value *value) {
    if (value && value->kind == SCRIPTUM_VALUE_OPTIONAL) {
        return (scriptum_optional *)value->payload;
    }
    return NULL;
}

static void scriptum_rt_write_escaped(FILE *stream, const char *data, uint64_t length) {
    fputc('"', stream);
    if (data != NULL) {
        for (uint64_t i = 0; i < length; ++i) {
            unsigned char ch = (unsigned char)data[i];
            switch (ch) {
                case '\\':
                case '"':
                    fputc('\\', stream);
                    fputc((int)ch, stream);
                    break;
                case '\b':
                    fputs("\\b", stream);
                    break;
                case '\f':
                    fputs("\\f", stream);
                    break;
                case '\n':
                    fputs("\\n", stream);
                    break;
                case '\r':
                    fputs("\\r", stream);
                    break;
                case '\t':
                    fputs("\\t", stream);
                    break;
                default:
                    if (ch < 0x20) {
                        fprintf(stream, "\\u%04X", ch);
                    } else {
                        fputc(ch, stream);
                    }
                    break;
            }
        }
    }
    fputc('"', stream);
}

static void scriptum_rt_dump_text(FILE *stream, scriptum_text *text) {
    if (text == NULL || text->data == NULL) {
        scriptum_rt_write_escaped(stream, "", 0);
        return;
    }
    scriptum_rt_write_escaped(stream, text->data, text->length);
}

static void scriptum_rt_dump_array(FILE *stream, scriptum_array *array) {
    if (array == NULL || array->items == NULL || array->length == 0) {
        fputs("[]", stream);
        return;
    }
    fputc('[', stream);
    for (uint64_t i = 0; i < array->length; ++i) {
        if (i > 0) {
            fputc(',', stream);
        }
        scriptum_rt_dump_value(stream, array->items[i]);
    }
    fputc(']', stream);
}

static void scriptum_rt_dump_object(FILE *stream, scriptum_object *object) {
    if (object == NULL || object->entries == NULL || object->length == 0) {
        fputs("{}", stream);
        return;
    }
    fputc('{', stream);
    for (uint64_t i = 0; i < object->length; ++i) {
        if (i > 0) {
            fputc(',', stream);
        }
        scriptum_object_entry *entry = &object->entries[i];
        if (entry->key) {
            scriptum_rt_write_escaped(stream, entry->key->data, entry->key->length);
        } else {
            scriptum_rt_write_escaped(stream, "", 0);
        }
        fputc(':', stream);
        scriptum_rt_dump_value(stream, entry->value);
    }
    fputc('}', stream);
}

static void scriptum_rt_dump_value(FILE *stream, scriptum_value value) {
    switch (value.kind) {
        case SCRIPTUM_VALUE_NUMBER:
            fprintf(stream, "%.17g", value.number);
            break;
        case SCRIPTUM_VALUE_BOOLEAN:
            fputs(value.boolean ? "true" : "false", stream);
            break;
        case SCRIPTUM_VALUE_TEXT:
            scriptum_rt_dump_text(stream, (scriptum_text *)value.payload);
            break;
        case SCRIPTUM_VALUE_ARRAY:
            scriptum_rt_dump_array(stream, (scriptum_array *)value.payload);
            break;
        case SCRIPTUM_VALUE_OBJECT:
            scriptum_rt_dump_object(stream, (scriptum_object *)value.payload);
            break;
        case SCRIPTUM_VALUE_OPTIONAL: {
            scriptum_optional *opt = (scriptum_optional *)value.payload;
            if (opt && opt->is_present) {
                scriptum_rt_dump_value(stream, opt->value);
            } else {
                fputs("null", stream);
            }
            break;
        }
        case SCRIPTUM_VALUE_NULL:
            fputs("null", stream);
            break;
        case SCRIPTUM_VALUE_LAMBDA:
            fputs("\"lambda\"", stream);
            break;
        default:
            fputs("null", stream);
            break;
    }
}

void scriptum_rt_dump(scriptum_value value) {
    const char *path = getenv("SCRIPTUM_LLVM_RESULT");
    FILE *stream = stdout;
    if (path && *path) {
        FILE *file = fopen(path, "wb");
        if (file != NULL) {
            stream = file;
        }
    }
    scriptum_rt_dump_value(stream, value);
    fputc('\n', stream);
    if (stream != stdout) {
        fclose(stream);
    } else {
        fflush(stream);
    }
}

static void scriptum_sb_init(scriptum_string_builder *builder) {
    if (builder == NULL) {
        return;
    }
    builder->data = NULL;
    builder->length = 0;
    builder->capacity = 0;
}

static void scriptum_sb_reset(scriptum_string_builder *builder) {
    if (builder == NULL) {
        return;
    }
    if (builder->data != NULL) {
        scriptum_release(builder->data);
    }
    builder->data = NULL;
    builder->length = 0;
    builder->capacity = 0;
}

static int scriptum_sb_reserve(scriptum_string_builder *builder, uint64_t capacity) {
    if (builder == NULL) {
        return 0;
    }
    if (capacity <= builder->capacity) {
        return 1;
    }
    char *next = (char *)scriptum_alloc(capacity > 0 ? capacity : 1);
    if (next == NULL) {
        return 0;
    }
    if (builder->data && builder->length > 0) {
        memcpy(next, builder->data, (size_t)builder->length);
    }
    if (builder->data) {
        scriptum_release(builder->data);
    }
    builder->data = next;
    builder->capacity = capacity;
    return 1;
}

static void scriptum_sb_append_bytes(scriptum_string_builder *builder, const char *data, uint64_t length) {
    if (builder == NULL || data == NULL || length == 0) {
        return;
    }
    uint64_t needed = builder->length + length;
    uint64_t capacity = builder->capacity ? builder->capacity : 64;
    while (capacity < needed) {
        capacity *= 2;
    }
    if (!scriptum_sb_reserve(builder, capacity)) {
        return;
    }
    memcpy(builder->data + builder->length, data, (size_t)length);
    builder->length = needed;
}

static void scriptum_sb_append_char(scriptum_string_builder *builder, char ch) {
    scriptum_sb_append_bytes(builder, &ch, 1);
}

static void scriptum_sb_append_cstr(scriptum_string_builder *builder, const char *text) {
    if (text == NULL) {
        return;
    }
    scriptum_sb_append_bytes(builder, text, (uint64_t)strlen(text));
}

static void scriptum_rt_format_value(scriptum_string_builder *builder, const scriptum_value *value) {
    if (builder == NULL || value == NULL) {
        return;
    }
    switch (value->kind) {
        case SCRIPTUM_VALUE_NUMBER: {
            char buffer[64];
            snprintf(buffer, sizeof(buffer), "%.15g", value->number);
            scriptum_sb_append_cstr(builder, buffer);
            break;
        }
        case SCRIPTUM_VALUE_BOOLEAN:
            scriptum_sb_append_cstr(builder, value->boolean ? "verum" : "falsum");
            break;
        case SCRIPTUM_VALUE_TEXT: {
            scriptum_text *text = scriptum_value_expect_text(value);
            if (text && text->data && text->length > 0) {
                scriptum_sb_append_bytes(builder, text->data, text->length);
            }
            break;
        }
        case SCRIPTUM_VALUE_ARRAY: {
            scriptum_array *array = scriptum_value_expect_array(value);
            scriptum_sb_append_char(builder, '[');
            if (array && array->items) {
                for (uint64_t i = 0; i < array->length; ++i) {
                    if (i > 0) {
                        scriptum_sb_append_cstr(builder, ", ");
                    }
                    scriptum_rt_format_value(builder, &array->items[i]);
                }
            }
            scriptum_sb_append_char(builder, ']');
            break;
        }
        case SCRIPTUM_VALUE_OBJECT: {
            scriptum_object *object = scriptum_value_expect_object(value);
            scriptum_sb_append_char(builder, '{');
            if (object && object->entries) {
                for (uint64_t i = 0; i < object->length; ++i) {
                    if (i > 0) {
                        scriptum_sb_append_cstr(builder, ", ");
                    }
                    scriptum_object_entry *entry = &object->entries[i];
                    if (entry->key && entry->key->data && entry->key->length > 0) {
                        scriptum_sb_append_bytes(builder, entry->key->data, entry->key->length);
                    }
                    scriptum_sb_append_cstr(builder, ": ");
                    scriptum_rt_format_value(builder, &entry->value);
                }
            }
            scriptum_sb_append_char(builder, '}');
            break;
        }
        case SCRIPTUM_VALUE_OPTIONAL: {
            scriptum_optional *optional = scriptum_value_expect_optional(value);
            if (optional && optional->is_present) {
                scriptum_rt_format_value(builder, &optional->value);
            } else {
                scriptum_sb_append_cstr(builder, "nullum");
            }
            break;
        }
        case SCRIPTUM_VALUE_LAMBDA:
            scriptum_sb_append_cstr(builder, "<lambda>");
            break;
        case SCRIPTUM_VALUE_NULL:
        case SCRIPTUM_VALUE_UNDEFINED:
            scriptum_sb_append_cstr(builder, "nullum");
            break;
        default:
            scriptum_sb_append_cstr(builder, "nullum");
            break;
    }
}

static int scriptum_rt_truthy(const scriptum_value *value) {
    if (value == NULL) {
        return 0;
    }
    switch (value->kind) {
        case SCRIPTUM_VALUE_BOOLEAN:
            return value->boolean != 0;
        case SCRIPTUM_VALUE_NUMBER:
            return value->number != 0.0;
        case SCRIPTUM_VALUE_TEXT: {
            scriptum_text *text = scriptum_value_expect_text(value);
            return text && text->length > 0;
        }
        case SCRIPTUM_VALUE_ARRAY: {
            scriptum_array *array = scriptum_value_expect_array(value);
            return array && array->length > 0;
        }
        case SCRIPTUM_VALUE_OBJECT: {
            scriptum_object *object = scriptum_value_expect_object(value);
            return object && object->length > 0;
        }
        case SCRIPTUM_VALUE_OPTIONAL: {
            scriptum_optional *optional = scriptum_value_expect_optional(value);
            return optional && optional->is_present && scriptum_rt_truthy(&optional->value);
        }
        case SCRIPTUM_VALUE_NULL:
            return 0;
        case SCRIPTUM_VALUE_LAMBDA:
            return value->payload != NULL;
        default:
            return value->payload != NULL;
    }
}

static int scriptum_rt_parse_number(const scriptum_value *value, double *out_number) {
    if (out_number) {
        *out_number = 0.0;
    }
    if (value == NULL) {
        return 0;
    }
    if (value->kind == SCRIPTUM_VALUE_NUMBER) {
        if (out_number) {
            *out_number = value->number;
        }
        return 1;
    }
    if (value->kind == SCRIPTUM_VALUE_BOOLEAN) {
        if (out_number) {
            *out_number = value->boolean ? 1.0 : 0.0;
        }
        return 1;
    }
    if (value->kind == SCRIPTUM_VALUE_TEXT) {
        scriptum_text *text = scriptum_value_expect_text(value);
        if (text == NULL || text->length == 0 || text->data == NULL) {
            return 0;
        }
        uint64_t len = text->length;
        char *buffer = (char *)scriptum_alloc(len + 1);
        if (buffer == NULL) {
            return 0;
        }
        memcpy(buffer, text->data, (size_t)len);
        buffer[len] = '\0';
        char *endptr = NULL;
        double parsed = strtod(buffer, &endptr);
        int ok = endptr != buffer;
        if (ok && endptr != NULL) {
            while (*endptr != '\0') {
                if (!isspace((unsigned char)*endptr)) {
                    ok = 0;
                    break;
                }
                endptr++;
            }
        }
        if (ok && out_number) {
            *out_number = parsed;
        }
        scriptum_release(buffer);
        return ok;
    }
    return 0;
}

static int scriptum_rt_parse_integer(const scriptum_value *value, int64_t *out_value) {
    double number = 0.0;
    int ok = scriptum_rt_parse_number(value, &number);
    if (out_value) {
        *out_value = (int64_t)number;
    }
    return ok;
}

static scriptum_text *scriptum_rt_text_from_value(const scriptum_value *value) {
    scriptum_string_builder builder;
    scriptum_sb_init(&builder);
    scriptum_rt_format_value(&builder, value);
    scriptum_text *text = scriptum_text_new(builder.data, builder.length);
    scriptum_sb_reset(&builder);
    if (text == NULL) {
        text = scriptum_text_new("", 0);
    }
    return text;
}

static scriptum_text *scriptum_rt_read_input_line(void) {
    scriptum_string_builder builder;
    scriptum_sb_init(&builder);
    int ch;
    while ((ch = fgetc(stdin)) != EOF) {
        if (ch == '\r') {
            int next = fgetc(stdin);
            if (next != '\n' && next != EOF) {
                ungetc(next, stdin);
            }
            break;
        }
        if (ch == '\n') {
            break;
        }
        scriptum_sb_append_char(&builder, (char)ch);
    }
    scriptum_text *line = scriptum_text_new(builder.data, builder.length);
    scriptum_sb_reset(&builder);
    if (line == NULL) {
        line = scriptum_text_new("", 0);
    }
    return line;
}

static scriptum_value scriptum_rt_arg(scriptum_value *args, uint64_t argc, uint64_t index) {
    if (args == NULL || index >= argc) {
        return scriptum_value_null();
    }
    return args[index];
}

static void scriptum_rt_sort_entries(scriptum_sort_entry *entries, uint64_t length, int reverse) {
    if (entries == NULL || length < 2) {
        return;
    }
    for (uint64_t i = 1; i < length; ++i) {
        scriptum_sort_entry current = entries[i];
        int64_t j = (int64_t)i - 1;
        while (j >= 0) {
            int cmp = 0;
            if (entries[j].key_text == NULL && current.key_text == NULL) {
                cmp = 0;
            } else if (entries[j].key_text == NULL) {
                cmp = -1;
            } else if (current.key_text == NULL) {
                cmp = 1;
            } else {
                cmp = scriptum_text_compare(entries[j].key_text, current.key_text);
            }
            if (reverse) {
                cmp = -cmp;
            }
            if (cmp <= 0) {
                break;
            }
            entries[j + 1] = entries[j];
            j--;
        }
        entries[j + 1] = current;
    }
}

static scriptum_text *scriptum_rt_text_slice(scriptum_text *text, uint64_t start, uint64_t length) {
    if (text == NULL || start > text->length) {
        return scriptum_text_new("", 0);
    }
    if (start + length > text->length) {
        length = text->length - start;
    }
    if (length == 0) {
        return scriptum_text_new("", 0);
    }
    scriptum_text *result = scriptum_text_new(text->data + start, length);
    return result ? result : scriptum_text_new("", 0);
}

static uint64_t scriptum_rt_text_find(scriptum_text *text, scriptum_text *pattern, uint64_t start) {
    if (text == NULL || pattern == NULL || pattern->length == 0 || pattern->length > text->length) {
        return UINT64_MAX;
    }
    if (start >= text->length) {
        return UINT64_MAX;
    }
    uint64_t limit = text->length - pattern->length;
    for (uint64_t index = start; index <= limit; ++index) {
        if (memcmp(text->data + index, pattern->data, (size_t)pattern->length) == 0) {
            return index;
        }
    }
    return UINT64_MAX;
}

static int scriptum_rt_values_equal(const scriptum_value *lhs, const scriptum_value *rhs) {
    if (lhs == NULL || rhs == NULL) {
        return 0;
    }
    if (lhs->kind != rhs->kind) {
        return 0;
    }
    switch (lhs->kind) {
        case SCRIPTUM_VALUE_NUMBER:
            return lhs->number == rhs->number;
        case SCRIPTUM_VALUE_BOOLEAN:
            return lhs->boolean == rhs->boolean;
        case SCRIPTUM_VALUE_TEXT: {
            scriptum_text *lt = scriptum_value_expect_text(lhs);
            scriptum_text *rt = scriptum_value_expect_text(rhs);
            if (lt == NULL || rt == NULL) {
                return lt == rt;
            }
            if (lt->length != rt->length) {
                return 0;
            }
            if (lt->length == 0) {
                return 1;
            }
            return memcmp(lt->data, rt->data, (size_t)lt->length) == 0;
        }
        case SCRIPTUM_VALUE_NULL:
            return 1;
        default:
            return lhs->payload == rhs->payload;
    }
}

scriptum_value scriptum_rt_scribe(scriptum_value *args, uint64_t argc) {
    for (uint64_t i = 0; i < argc; ++i) {
        if (i > 0) {
            fputc(' ', stdout);
        }
        scriptum_text *text = scriptum_rt_text_from_value(&args[i]);
        if (text && text->data && text->length > 0) {
            fwrite(text->data, 1, (size_t)text->length, stdout);
        }
        scriptum_text_release(text);
    }
    fputc('\n', stdout);
    fflush(stdout);
    return scriptum_value_null();
}

scriptum_value scriptum_rt_longitudo(scriptum_value *args, uint64_t argc) {
    scriptum_value target = scriptum_rt_arg(args, argc, 0);
    uint64_t length = 0;
    scriptum_text *text = scriptum_value_expect_text(&target);
    if (text != NULL) {
        length = text->length;
    } else {
        scriptum_array *array = scriptum_value_expect_array(&target);
        if (array != NULL) {
            length = array->length;
        }
    }
    return scriptum_value_number((double)length);
}

scriptum_value scriptum_rt_numerus(scriptum_value *args, uint64_t argc) {
    scriptum_value value = scriptum_rt_arg(args, argc, 0);
    double number = 0.0;
    scriptum_rt_parse_number(&value, &number);
    return scriptum_value_number(number);
}

scriptum_value scriptum_rt_textus(scriptum_value *args, uint64_t argc) {
    scriptum_value value = scriptum_rt_arg(args, argc, 0);
    scriptum_text *text = scriptum_rt_text_from_value(&value);
    if (text == NULL) {
        return scriptum_value_null();
    }
    return scriptum_value_text(text);
}

scriptum_value scriptum_rt_booleanum(scriptum_value *args, uint64_t argc) {
    scriptum_value value = scriptum_rt_arg(args, argc, 0);
    return scriptum_value_boolean(scriptum_rt_truthy(&value));
}

scriptum_value scriptum_rt_ambitus(scriptum_value *args, uint64_t argc) {
    scriptum_value start_value = scriptum_rt_arg(args, argc, 0);
    scriptum_value end_value = scriptum_rt_arg(args, argc, 1);
    scriptum_value step_value = scriptum_rt_arg(args, argc, 2);
    int64_t start = 0;
    int64_t end = 0;
    int64_t step = 1;
    scriptum_rt_parse_integer(&start_value, &start);
    scriptum_rt_parse_integer(&end_value, &end);
    if (argc >= 3) {
        scriptum_rt_parse_integer(&step_value, &step);
    }
    if (step == 0) {
        step = 1;
    }
    scriptum_array *result = scriptum_array_new(0);
    if (result == NULL) {
        return scriptum_value_null();
    }
    if (step > 0) {
        for (int64_t current = start; current < end; current += step) {
            scriptum_array_push(result, scriptum_value_number((double)current));
        }
    } else {
        for (int64_t current = start; current > end; current += step) {
            scriptum_array_push(result, scriptum_value_number((double)current));
        }
    }
    return scriptum_value_array(result);
}

scriptum_value scriptum_rt_summa(scriptum_value *args, uint64_t argc) {
    scriptum_value array_value = scriptum_rt_arg(args, argc, 0);
    scriptum_array *array = scriptum_value_expect_array(&array_value);
    if (array == NULL) {
        return scriptum_value_number(0.0);
    }
    double total = 0.0;
    for (uint64_t i = 0; i < array->length; ++i) {
        double number = 0.0;
        scriptum_rt_parse_number(&array->items[i], &number);
        total += number;
    }
    return scriptum_value_number(total);
}

scriptum_value scriptum_rt_minimum(scriptum_value *args, uint64_t argc) {
    scriptum_value array_value = scriptum_rt_arg(args, argc, 0);
    scriptum_array *array = scriptum_value_expect_array(&array_value);
    if (array == NULL || array->length == 0) {
        return scriptum_value_null();
    }
    double best = 0.0;
    int has_value = 0;
    for (uint64_t i = 0; i < array->length; ++i) {
        double current = 0.0;
        if (!scriptum_rt_parse_number(&array->items[i], &current)) {
            continue;
        }
        if (!has_value || current < best) {
            best = current;
            has_value = 1;
        }
    }
    return has_value ? scriptum_value_number(best) : scriptum_value_null();
}

scriptum_value scriptum_rt_maximum(scriptum_value *args, uint64_t argc) {
    scriptum_value array_value = scriptum_rt_arg(args, argc, 0);
    scriptum_array *array = scriptum_value_expect_array(&array_value);
    if (array == NULL || array->length == 0) {
        return scriptum_value_null();
    }
    double best = 0.0;
    int has_value = 0;
    for (uint64_t i = 0; i < array->length; ++i) {
        double current = 0.0;
        if (!scriptum_rt_parse_number(&array->items[i], &current)) {
            continue;
        }
        if (!has_value || current > best) {
            best = current;
            has_value = 1;
        }
    }
    return has_value ? scriptum_value_number(best) : scriptum_value_null();
}

scriptum_value scriptum_rt_absolutum(scriptum_value *args, uint64_t argc) {
    scriptum_value value = scriptum_rt_arg(args, argc, 0);
    double number = 0.0;
    scriptum_rt_parse_number(&value, &number);
    return scriptum_value_number(fabs(number));
}

scriptum_value scriptum_rt_aliquod(scriptum_value *args, uint64_t argc) {
    scriptum_value array_value = scriptum_rt_arg(args, argc, 0);
    scriptum_array *array = scriptum_value_expect_array(&array_value);
    if (array == NULL) {
        return scriptum_value_boolean(0);
    }
    for (uint64_t i = 0; i < array->length; ++i) {
        if (scriptum_rt_truthy(&array->items[i])) {
            return scriptum_value_boolean(1);
        }
    }
    return scriptum_value_boolean(0);
}

scriptum_value scriptum_rt_omnia(scriptum_value *args, uint64_t argc) {
    scriptum_value array_value = scriptum_rt_arg(args, argc, 0);
    scriptum_array *array = scriptum_value_expect_array(&array_value);
    if (array == NULL || array->length == 0) {
        return scriptum_value_boolean(0);
    }
    for (uint64_t i = 0; i < array->length; ++i) {
        if (!scriptum_rt_truthy(&array->items[i])) {
            return scriptum_value_boolean(0);
        }
    }
    return scriptum_value_boolean(1);
}

scriptum_value scriptum_rt_lege(scriptum_value *args, uint64_t argc) {
    scriptum_value prompt_value = scriptum_rt_arg(args, argc, 0);
    scriptum_text *prompt_text = scriptum_value_expect_text(&prompt_value);
    int owns_prompt = 0;
    if (prompt_text == NULL && prompt_value.kind != SCRIPTUM_VALUE_NULL) {
        prompt_text = scriptum_rt_text_from_value(&prompt_value);
        owns_prompt = 1;
    }
    if (prompt_text && prompt_text->data && prompt_text->length > 0) {
        fwrite(prompt_text->data, 1, (size_t)prompt_text->length, stdout);
        fflush(stdout);
    }
    if (owns_prompt && prompt_text) {
        scriptum_text_release(prompt_text);
    }
    scriptum_text *line = scriptum_rt_read_input_line();
    if (line == NULL) {
        line = scriptum_text_new("", 0);
    }
    return scriptum_value_text(line);
}

scriptum_value scriptum_rt_enumera(scriptum_value *args, uint64_t argc) {
    scriptum_value array_value = scriptum_rt_arg(args, argc, 0);
    scriptum_array *source = scriptum_value_expect_array(&array_value);
    if (source == NULL) {
        return scriptum_value_array(scriptum_array_new(0));
    }
    scriptum_array *result = scriptum_array_new(source->length);
    if (result == NULL) {
        return scriptum_value_null();
    }
    for (uint64_t i = 0; i < source->length; ++i) {
        scriptum_array *pair = scriptum_array_new(2);
        if (pair == NULL) {
            continue;
        }
        scriptum_array_push(pair, scriptum_value_number((double)i));
        scriptum_array_push(pair, source->items[i]);
        scriptum_value wrapped = scriptum_value_array(pair);
        scriptum_array_push(result, wrapped);
        scriptum_array_release(pair);
    }
    return scriptum_value_array(result);
}

scriptum_value scriptum_rt_coniunge(scriptum_value *args, uint64_t argc) {
    scriptum_value left_value = scriptum_rt_arg(args, argc, 0);
    scriptum_value right_value = scriptum_rt_arg(args, argc, 1);
    scriptum_array *left = scriptum_value_expect_array(&left_value);
    scriptum_array *right = scriptum_value_expect_array(&right_value);
    if (left == NULL || right == NULL) {
        return scriptum_value_array(scriptum_array_new(0));
    }
    uint64_t limit = left->length < right->length ? left->length : right->length;
    scriptum_array *result = scriptum_array_new(limit);
    if (result == NULL) {
        return scriptum_value_null();
    }
    for (uint64_t i = 0; i < limit; ++i) {
        scriptum_array *pair = scriptum_array_new(2);
        if (pair == NULL) {
            continue;
        }
        scriptum_array_push(pair, left->items[i]);
        scriptum_array_push(pair, right->items[i]);
        scriptum_value wrapped = scriptum_value_array(pair);
        scriptum_array_push(result, wrapped);
        scriptum_array_release(pair);
    }
    return scriptum_value_array(result);
}

scriptum_value scriptum_rt_applica(scriptum_value *args, uint64_t argc) {
    scriptum_value array_value = scriptum_rt_arg(args, argc, 0);
    scriptum_value func_value = scriptum_rt_arg(args, argc, 1);
    scriptum_array *source = scriptum_value_expect_array(&array_value);
    scriptum_lambda *lambda = scriptum_value_expect_lambda(&func_value);
    if (source == NULL || lambda == NULL) {
        return scriptum_value_array(scriptum_array_new(0));
    }
    scriptum_array *result = scriptum_array_new(source->length);
    if (result == NULL) {
        return scriptum_value_null();
    }
    for (uint64_t i = 0; i < source->length; ++i) {
        scriptum_value argument = scriptum_value_clone(&source->items[i]);
        scriptum_value call_result = scriptum_lambda_call(lambda, &argument, 1);
        scriptum_value_dispose(&argument);
        scriptum_array_push(result, call_result);
        scriptum_value_dispose(&call_result);
    }
    return scriptum_value_array(result);
}

scriptum_value scriptum_rt_filtra(scriptum_value *args, uint64_t argc) {
    scriptum_value array_value = scriptum_rt_arg(args, argc, 0);
    scriptum_value func_value = scriptum_rt_arg(args, argc, 1);
    scriptum_array *source = scriptum_value_expect_array(&array_value);
    scriptum_lambda *lambda = scriptum_value_expect_lambda(&func_value);
    if (source == NULL || lambda == NULL) {
        return scriptum_value_array(scriptum_array_new(0));
    }
    scriptum_array *result = scriptum_array_new(source->length);
    if (result == NULL) {
        return scriptum_value_null();
    }
    for (uint64_t i = 0; i < source->length; ++i) {
        scriptum_value argument = scriptum_value_clone(&source->items[i]);
        scriptum_value decision = scriptum_lambda_call(lambda, &argument, 1);
        scriptum_value_dispose(&argument);
        int keep = scriptum_rt_truthy(&decision);
        scriptum_value_dispose(&decision);
        if (keep) {
            scriptum_array_push(result, source->items[i]);
        }
    }
    return scriptum_value_array(result);
}

scriptum_value scriptum_rt_ordina(scriptum_value *args, uint64_t argc) {
    scriptum_value array_value = scriptum_rt_arg(args, argc, 0);
    scriptum_array *source = scriptum_value_expect_array(&array_value);
    if (source == NULL) {
        return scriptum_value_array(scriptum_array_new(0));
    }
    scriptum_value key_value = scriptum_rt_arg(args, argc, 1);
    scriptum_lambda *key_lambda = NULL;
    if (key_value.kind == SCRIPTUM_VALUE_LAMBDA) {
        key_lambda = scriptum_value_expect_lambda(&key_value);
    }
    scriptum_value reverse_value = scriptum_rt_arg(args, argc, 2);
    int reverse = scriptum_rt_truthy(&reverse_value);
    uint64_t length = source->length;
    scriptum_sort_entry *entries = NULL;
    if (length > 0) {
        entries = (scriptum_sort_entry *)scriptum_alloc(sizeof(scriptum_sort_entry) * length);
        if (entries == NULL) {
            return scriptum_value_null();
        }
        memset(entries, 0, sizeof(scriptum_sort_entry) * length);
    }
    for (uint64_t i = 0; i < length; ++i) {
        entries[i].value = scriptum_value_clone(&source->items[i]);
        if (key_lambda) {
            scriptum_value argument = scriptum_value_clone(&source->items[i]);
            scriptum_value key_result = scriptum_lambda_call(key_lambda, &argument, 1);
            scriptum_value_dispose(&argument);
            entries[i].key_text = scriptum_rt_text_from_value(&key_result);
            scriptum_value_dispose(&key_result);
        } else {
            entries[i].key_text = scriptum_rt_text_from_value(&source->items[i]);
        }
    }
    scriptum_rt_sort_entries(entries, length, reverse);
    scriptum_array *result = scriptum_array_new(length);
    if (result == NULL) {
        for (uint64_t i = 0; i < length; ++i) {
            scriptum_value_dispose(&entries[i].value);
            if (entries[i].key_text) {
                scriptum_text_release(entries[i].key_text);
            }
        }
        scriptum_release(entries);
        return scriptum_value_null();
    }
    for (uint64_t i = 0; i < length; ++i) {
        scriptum_array_push(result, entries[i].value);
        scriptum_value_dispose(&entries[i].value);
        if (entries[i].key_text) {
            scriptum_text_release(entries[i].key_text);
        }
    }
    if (entries) {
        scriptum_release(entries);
    }
    return scriptum_value_array(result);
}

scriptum_value scriptum_rt_array_adde(scriptum_array *array, scriptum_value *args, uint64_t argc) {
    if (array == NULL) {
        return scriptum_value_null();
    }
    scriptum_value value = scriptum_rt_arg(args, argc, 0);
    scriptum_array_push(array, value);
    return scriptum_value_null();
}

scriptum_value scriptum_rt_array_exime(scriptum_array *array, scriptum_value *args, uint64_t argc) {
    (void)args;
    (void)argc;
    if (array == NULL || array->length == 0) {
        return scriptum_value_null();
    }
    uint64_t index = array->length - 1;
    scriptum_value result = scriptum_value_clone(&array->items[index]);
    scriptum_value_dispose(&array->items[index]);
    array->length--;
    return result;
}

scriptum_value scriptum_rt_array_extende(scriptum_array *array, scriptum_value *args, uint64_t argc) {
    if (array == NULL) {
        return scriptum_value_null();
    }
    scriptum_value other_value = scriptum_rt_arg(args, argc, 0);
    scriptum_array *other = scriptum_value_expect_array(&other_value);
    if (other == NULL) {
        return scriptum_value_null();
    }
    for (uint64_t i = 0; i < other->length; ++i) {
        scriptum_array_push(array, other->items[i]);
    }
    return scriptum_value_null();
}

scriptum_value scriptum_rt_array_inserta(scriptum_array *array, scriptum_value *args, uint64_t argc) {
    if (array == NULL) {
        return scriptum_value_null();
    }
    scriptum_value index_value = scriptum_rt_arg(args, argc, 0);
    scriptum_value value = scriptum_rt_arg(args, argc, 1);
    int64_t index = 0;
    scriptum_rt_parse_integer(&index_value, &index);
    if (index < 0) {
        index = 0;
    } else if ((uint64_t)index > array->length) {
        index = (int64_t)array->length;
    }
    if (array->length == array->capacity) {
        uint64_t next_capacity = array->capacity ? array->capacity * 2 : 4;
        if (!scriptum_array_reserve(array, next_capacity)) {
            return scriptum_value_null();
        }
    }
    for (uint64_t i = array->length; i > (uint64_t)index; --i) {
        array->items[i] = array->items[i - 1];
    }
    array->items[index] = scriptum_value_clone(&value);
    array->length++;
    return scriptum_value_null();
}

scriptum_value scriptum_rt_array_remove(scriptum_array *array, scriptum_value *args, uint64_t argc) {
    if (array == NULL) {
        return scriptum_value_null();
    }
    scriptum_value target = scriptum_rt_arg(args, argc, 0);
    for (uint64_t i = 0; i < array->length; ++i) {
        if (scriptum_rt_values_equal(&array->items[i], &target)) {
            scriptum_value_dispose(&array->items[i]);
            for (uint64_t j = i; j + 1 < array->length; ++j) {
                array->items[j] = array->items[j + 1];
            }
            array->length--;
            break;
        }
    }
    return scriptum_value_null();
}

scriptum_value scriptum_rt_array_purga(scriptum_array *array, scriptum_value *args, uint64_t argc) {
    (void)args;
    (void)argc;
    if (array == NULL) {
        return scriptum_value_null();
    }
    for (uint64_t i = 0; i < array->length; ++i) {
        scriptum_value_dispose(&array->items[i]);
    }
    array->length = 0;
    return scriptum_value_null();
}

scriptum_value scriptum_rt_text_divide(scriptum_text *text, scriptum_value *args, uint64_t argc) {
    scriptum_array *result = scriptum_array_new(0);
    if (result == NULL) {
        return scriptum_value_null();
    }
    if (text == NULL) {
        return scriptum_value_array(result);
    }
    scriptum_text *separator = NULL;
    int owns_separator = 0;
    if (argc > 0) {
        scriptum_value sep_value = scriptum_rt_arg(args, argc, 0);
        separator = scriptum_value_expect_text(&sep_value);
        if (separator == NULL && sep_value.kind != SCRIPTUM_VALUE_NULL) {
            separator = scriptum_rt_text_from_value(&sep_value);
            owns_separator = 1;
        }
    }
    if (separator == NULL) {
        separator = scriptum_text_new(" ", 1);
        owns_separator = 1;
    }
    if (separator == NULL || separator->length == 0) {
        scriptum_text *piece = scriptum_rt_text_slice(text, 0, text->length);
        scriptum_value wrap = scriptum_value_text(piece);
        scriptum_array_push(result, wrap);
        scriptum_text_release(piece);
    } else {
        uint64_t start = 0;
        while (start <= text->length) {
            uint64_t pos = scriptum_rt_text_find(text, separator, start);
            if (pos == UINT64_MAX) {
                scriptum_text *piece = scriptum_rt_text_slice(text, start, text->length - start);
                scriptum_value wrap = scriptum_value_text(piece);
                scriptum_array_push(result, wrap);
                scriptum_text_release(piece);
                break;
            }
            scriptum_text *piece = scriptum_rt_text_slice(text, start, pos - start);
            scriptum_value wrap = scriptum_value_text(piece);
            scriptum_array_push(result, wrap);
            scriptum_text_release(piece);
            start = pos + separator->length;
        }
    }
    if (owns_separator && separator) {
        scriptum_text_release(separator);
    }
    return scriptum_value_array(result);
}

scriptum_value scriptum_rt_text_coniunge(scriptum_text *text, scriptum_value *args, uint64_t argc) {
    scriptum_value array_value = scriptum_rt_arg(args, argc, 0);
    scriptum_array *items = scriptum_value_expect_array(&array_value);
    if (items == NULL) {
        return scriptum_value_text(scriptum_text_new("", 0));
    }
    scriptum_string_builder builder;
    scriptum_sb_init(&builder);
    for (uint64_t i = 0; i < items->length; ++i) {
        if (i > 0 && text && text->data && text->length > 0) {
            scriptum_sb_append_bytes(&builder, text->data, text->length);
        }
        scriptum_text *entry = scriptum_value_expect_text(&items->items[i]);
        int release_entry = 0;
        if (entry == NULL) {
            entry = scriptum_rt_text_from_value(&items->items[i]);
            release_entry = 1;
        }
        if (entry && entry->data && entry->length > 0) {
            scriptum_sb_append_bytes(&builder, entry->data, entry->length);
        }
        if (release_entry && entry) {
            scriptum_text_release(entry);
        }
    }
    scriptum_text *result_text = scriptum_text_new(builder.data, builder.length);
    scriptum_sb_reset(&builder);
    return scriptum_value_text(result_text);
}

scriptum_value scriptum_rt_text_substitue(scriptum_text *text, scriptum_value *args, uint64_t argc) {
    scriptum_value old_value = scriptum_rt_arg(args, argc, 0);
    scriptum_value new_value = scriptum_rt_arg(args, argc, 1);
    scriptum_text *old_text = scriptum_value_expect_text(&old_value);
    scriptum_text *new_text = scriptum_value_expect_text(&new_value);
    if (text == NULL || old_text == NULL || old_text->length == 0 || new_text == NULL) {
        scriptum_text *copy = text ? scriptum_rt_text_slice(text, 0, text->length) : scriptum_text_new("", 0);
        return scriptum_value_text(copy);
    }
    scriptum_string_builder builder;
    scriptum_sb_init(&builder);
    uint64_t index = 0;
    while (index < text->length) {
        if (index <= text->length - old_text->length &&
            memcmp(text->data + index, old_text->data, (size_t)old_text->length) == 0) {
            scriptum_sb_append_bytes(&builder, new_text->data, new_text->length);
            index += old_text->length;
        } else {
            scriptum_sb_append_char(&builder, text->data[index]);
            index++;
        }
    }
    scriptum_text *result_text = scriptum_text_new(builder.data, builder.length);
    scriptum_sb_reset(&builder);
    return scriptum_value_text(result_text);
}

scriptum_value scriptum_rt_text_ad_minusculas(scriptum_text *text, scriptum_value *args, uint64_t argc) {
    (void)args;
    (void)argc;
    if (text == NULL || text->length == 0) {
        return scriptum_value_text(scriptum_text_new("", 0));
    }
    scriptum_text *result = scriptum_text_new(text->data, text->length);
    if (result && result->data) {
        for (uint64_t i = 0; i < result->length; ++i) {
            result->data[i] = (char)tolower((unsigned char)result->data[i]);
        }
    }
    return scriptum_value_text(result);
}

scriptum_value scriptum_rt_text_ad_maiusculas(scriptum_text *text, scriptum_value *args, uint64_t argc) {
    (void)args;
    (void)argc;
    if (text == NULL || text->length == 0) {
        return scriptum_value_text(scriptum_text_new("", 0));
    }
    scriptum_text *result = scriptum_text_new(text->data, text->length);
    if (result && result->data) {
        for (uint64_t i = 0; i < result->length; ++i) {
            result->data[i] = (char)toupper((unsigned char)result->data[i]);
        }
    }
    return scriptum_value_text(result);
}

scriptum_value scriptum_rt_text_abscinde(scriptum_text *text, scriptum_value *args, uint64_t argc) {
    (void)args;
    (void)argc;
    if (text == NULL || text->length == 0) {
        return scriptum_value_text(scriptum_text_new("", 0));
    }
    uint64_t start = 0;
    while (start < text->length && isspace((unsigned char)text->data[start])) {
        start++;
    }
    if (start == text->length) {
        return scriptum_value_text(scriptum_text_new("", 0));
    }
    int64_t end = (int64_t)text->length - 1;
    while (end >= 0 && isspace((unsigned char)text->data[end])) {
        end--;
    }
    scriptum_text *result = scriptum_rt_text_slice(text, start, (uint64_t)(end - (int64_t)start + 1));
    return scriptum_value_text(result);
}

static scriptum_value scriptum_value_clone(const scriptum_value *value) {
    if (value == NULL) {
        return scriptum_value_null();
    }
    scriptum_value copy = *value;
    switch (value->kind) {
        case SCRIPTUM_VALUE_TEXT:
            scriptum_text_retain((scriptum_text *)copy.payload);
            break;
        case SCRIPTUM_VALUE_ARRAY:
            scriptum_array_retain((scriptum_array *)copy.payload);
            break;
        case SCRIPTUM_VALUE_OBJECT:
            scriptum_object_retain((scriptum_object *)copy.payload);
            break;
        case SCRIPTUM_VALUE_LAMBDA:
            scriptum_lambda_retain((scriptum_lambda *)copy.payload);
            break;
        case SCRIPTUM_VALUE_OPTIONAL:
            scriptum_optional_retain((scriptum_optional *)copy.payload);
            break;
        default:
            break;
    }
    return copy;
}

static void scriptum_value_dispose(scriptum_value *value) {
    if (value == NULL) {
        return;
    }
    switch (value->kind) {
        case SCRIPTUM_VALUE_TEXT:
            scriptum_text_release((scriptum_text *)value->payload);
            break;
        case SCRIPTUM_VALUE_ARRAY:
            scriptum_array_release((scriptum_array *)value->payload);
            break;
        case SCRIPTUM_VALUE_OBJECT:
            scriptum_object_release((scriptum_object *)value->payload);
            break;
        case SCRIPTUM_VALUE_LAMBDA:
            scriptum_lambda_release((scriptum_lambda *)value->payload);
            break;
        case SCRIPTUM_VALUE_OPTIONAL:
            scriptum_optional_release((scriptum_optional *)value->payload);
            break;
        default:
            break;
    }
    value->kind = SCRIPTUM_VALUE_UNDEFINED;
    value->payload = NULL;
}
