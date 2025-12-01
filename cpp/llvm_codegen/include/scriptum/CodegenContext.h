#pragma once

#include <llvm/IR/IRBuilder.h>
#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/Module.h>

#include <memory>
#include <stack>
#include <string>
#include <unordered_map>
#include <vector>

namespace scriptum {

struct LoopContext {
    llvm::BasicBlock *breakBlock{};
    llvm::BasicBlock *continueBlock{};
};

class CodegenContext {
public:
    explicit CodegenContext(std::string moduleName);

    llvm::LLVMContext &llvmContext() { return *llvmCtx_; }
    llvm::Module &module() { return *module_; }
    llvm::IRBuilder<> &builder() { return builder_; }

    void pushScope();
    void popScope();
    void registerSymbol(const std::string &name, llvm::Value *value);
    llvm::Value *lookupSymbol(const std::string &name) const;

    void pushLoop(llvm::BasicBlock *breakBlock, llvm::BasicBlock *continueBlock);
    void popLoop();
    LoopContext currentLoop() const;

    llvm::AllocaInst *createEntryAlloca(llvm::Function *function,
                                        llvm::Type *type,
                                        const std::string &name);

private:
    std::unique_ptr<llvm::LLVMContext> llvmCtx_;
    std::unique_ptr<llvm::Module> module_;
    llvm::IRBuilder<> builder_;

    using Scope = std::unordered_map<std::string, llvm::Value *>;
    std::vector<Scope> scopes_;
    std::vector<LoopContext> loopStack_;
};

}  // namespace scriptum
