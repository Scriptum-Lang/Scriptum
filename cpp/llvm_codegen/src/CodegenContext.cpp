#include "scriptum/CodegenContext.h"

namespace scriptum {

CodegenContext::CodegenContext(std::string moduleName)
    : llvmCtx_(std::make_unique<llvm::LLVMContext>()),
      module_(std::make_unique<llvm::Module>(moduleName, *llvmCtx_)),
      builder_(*llvmCtx_) {
    pushScope();
}

void CodegenContext::pushScope() {
    scopes_.emplace_back();
}

void CodegenContext::popScope() {
    if (!scopes_.empty()) {
        scopes_.pop_back();
    }
}

void CodegenContext::registerSymbol(const std::string &name, llvm::Value *value) {
    scopes_.back()[name] = value;
}

llvm::Value *CodegenContext::lookupSymbol(const std::string &name) const {
    for (auto it = scopes_.rbegin(); it != scopes_.rend(); ++it) {
        auto found = it->find(name);
        if (found != it->end()) {
            return found->second;
        }
    }
    return nullptr;
}

void CodegenContext::pushLoop(llvm::BasicBlock *breakBlock, llvm::BasicBlock *continueBlock) {
    loopStack_.push_back(LoopContext{breakBlock, continueBlock});
}

void CodegenContext::popLoop() {
    if (!loopStack_.empty()) {
        loopStack_.pop_back();
    }
}

LoopContext CodegenContext::currentLoop() const {
    if (loopStack_.empty()) {
        return {};
    }
    return loopStack_.back();
}

llvm::AllocaInst *CodegenContext::createEntryAlloca(llvm::Function *function,
                                                    llvm::Type *type,
                                                    const std::string &name) {
    llvm::IRBuilder<> tmp(&function->getEntryBlock(),
                          function->getEntryBlock().begin());
    return tmp.CreateAlloca(type, nullptr, name);
}

}  // namespace scriptum
