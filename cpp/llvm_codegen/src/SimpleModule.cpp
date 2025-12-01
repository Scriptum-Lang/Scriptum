#include "scriptum/SimpleModule.h"

#include <llvm/IR/Constants.h>
#include <llvm/IR/Type.h>
#include <llvm/Support/raw_ostream.h>

#include <stdexcept>

namespace scriptum {

SimpleModuleEmitter::SimpleModuleEmitter(std::string moduleName)
    : context_(std::make_unique<llvm::LLVMContext>()),
      module_(std::make_unique<llvm::Module>(moduleName, *context_)) {}

void SimpleModuleEmitter::addFunction(const SimpleFunction &fn) {
    auto &ctx = *context_;
    auto doubleTy = llvm::Type::getDoubleTy(ctx);
    auto fnType = llvm::FunctionType::get(doubleTy, false);
    auto *function =
        llvm::Function::Create(fnType, llvm::GlobalValue::ExternalLinkage, fn.name, module_.get());
    auto *entry = llvm::BasicBlock::Create(ctx, "entry", function);
    llvm::IRBuilder<> builder(entry);
    llvm::Value *result = nullptr;
    if (fn.ret.isBinary) {
        auto *lhs = llvm::ConstantFP::get(doubleTy, fn.ret.lhs);
        auto *rhs = llvm::ConstantFP::get(doubleTy, fn.ret.rhs);
        result = builder.CreateFAdd(lhs, rhs, "tmp.add");
    } else {
        result = llvm::ConstantFP::get(doubleTy, fn.ret.lhs);
    }
    builder.CreateRet(result);
}

std::string SimpleModuleEmitter::render() const {
    std::string verifyErrors;
    llvm::raw_string_ostream errStream(verifyErrors);
    if (llvm::verifyModule(*module_, &errStream)) {
        throw std::runtime_error("llvm::verifyModule falhou: " + errStream.str());
    }
    std::string buffer;
    llvm::raw_string_ostream os(buffer);
    module_->print(os, nullptr);
    return os.str();
}

std::string emit_simple_module(const std::string &moduleName, const std::vector<SimpleFunction> &functions) {
    SimpleModuleEmitter emitter(moduleName);
    for (const auto &fn : functions) {
        emitter.addFunction(fn);
    }
    return emitter.render();
}

}  // namespace scriptum
