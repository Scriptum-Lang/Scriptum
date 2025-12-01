#pragma once

#include "CodegenContext.h"

namespace scriptum {

class Emitter {
public:
    explicit Emitter(CodegenContext &ctx) : ctx_(ctx) {}

    llvm::Type *mapType(const std::string &semanticType);
    llvm::Value *createCast(llvm::Value *value, llvm::Type *targetType);
    llvm::Value *emitNumericBinary(const std::string &op,
                                   llvm::Value *lhs,
                                   llvm::Value *rhs,
                                   bool isFloat);

private:
    CodegenContext &ctx_;
};

}  // namespace scriptum
