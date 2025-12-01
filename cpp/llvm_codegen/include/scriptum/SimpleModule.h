#pragma once

#include <llvm/IR/IRBuilder.h>
#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/Verifier.h>

#include <memory>
#include <string>
#include <vector>

namespace scriptum {

struct SimpleReturn {
    bool isBinary{false};
    double lhs{0.0};
    double rhs{0.0};
};

struct SimpleFunction {
    std::string name;
    SimpleReturn ret;
};

class SimpleModuleEmitter {
public:
    explicit SimpleModuleEmitter(std::string moduleName);

    void addFunction(const SimpleFunction &fn);
    std::string render() const;

private:
    std::unique_ptr<llvm::LLVMContext> context_;
    std::unique_ptr<llvm::Module> module_;
};

std::string emit_simple_module(const std::string &moduleName, const std::vector<SimpleFunction> &functions);

}  // namespace scriptum
