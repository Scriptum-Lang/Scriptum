#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <stdexcept>
#include <string>
#include <vector>

#include "scriptum/SimpleModule.h"

namespace py = pybind11;

namespace {

std::string type_name(py::handle obj) {
    py::object cls = obj.get_type();
    return py::cast<std::string>(cls.attr("__name__"));
}

double literal_value(py::handle literal) {
    if (type_name(literal) != "IrLiteral") {
        throw std::runtime_error("Literal esperado.");
    }
    return py::cast<double>(literal.attr("value"));
}

scriptum::SimpleFunction parse_function(py::handle func_obj) {
    scriptum::SimpleFunction fn;
    fn.name = py::cast<std::string>(func_obj.attr("name"));
    py::list body = func_obj.attr("body");
    if (py::len(body) == 0) {
        throw std::runtime_error("Functio sem corpo nao suportada.");
    }
    py::object ret_stmt = body[py::len(body) - 1];
    if (type_name(ret_stmt) != "IrReturn") {
        throw std::runtime_error("Somente retornos simples sao suportados.");
    }
    py::object value = ret_stmt.attr("value");
    if (value.is_none()) {
        fn.ret.isBinary = false;
        fn.ret.lhs = 0.0;
        return fn;
    }
    const auto expr_kind = type_name(value);
    if (expr_kind == "IrLiteral") {
        fn.ret.isBinary = false;
        fn.ret.lhs = literal_value(value);
        return fn;
    }
    if (expr_kind == "IrBinary") {
        std::string op = py::cast<std::string>(value.attr("operator"));
        if (op != "+" && op != "ADD") {
            throw std::runtime_error("Apenas somas sao suportadas pelo backend C++.");
        }
        auto left = value.attr("left");
        auto right = value.attr("right");
        fn.ret.isBinary = true;
        fn.ret.lhs = literal_value(left);
        fn.ret.rhs = literal_value(right);
        return fn;
    }
    throw std::runtime_error("Expressao de retorno nao suportada pelo backend C++.");
}

std::string emit_from_python(py::object module_ir, const std::string &module_name) {
    py::list functions = module_ir.attr("functions");
    if (py::len(functions) == 0) {
        throw std::runtime_error("Modulo precisa declarar ao menos uma functio.");
    }
    std::vector<scriptum::SimpleFunction> fns;
    fns.reserve(py::len(functions));
    for (auto &&fn_obj : functions) {
        fns.push_back(parse_function(fn_obj));
    }
    return scriptum::emit_simple_module(module_name, fns);
}

}  // namespace

PYBIND11_MODULE(scriptum_codegen_llvm_cpp_py, m) {
    m.doc() = "Scriptum LLVM C++ backend bindings";
    m.def("emit_module", &emit_from_python, py::arg("module_ir"), py::arg("module_name"));
}
