#include "scriptum/Emitter.h"

#include <llvm/IR/Constants.h>

namespace scriptum {

llvm::Type *Emitter::mapType(const std::string &semanticType) {
    if (semanticType == "numerus") {
        return llvm::Type::getDoubleTy(ctx_.llvmContext());
    }
    if (semanticType == "booleanum") {
        return llvm::Type::getInt1Ty(ctx_.llvmContext());
    }
    return llvm::Type::getVoidTy(ctx_.llvmContext());
}

llvm::Value *Emitter::createCast(llvm::Value *value, llvm::Type *targetType) {
    if (value->getType() == targetType) {
        return value;
    }
    if (value->getType()->isIntegerTy() && targetType->isDoubleTy()) {
        return ctx_.builder().CreateSIToFP(value, targetType, "sitofp.tmp");
    }
    if (value->getType()->isDoubleTy() && targetType->isIntegerTy(1)) {
        llvm::Value *cmp =
            ctx_.builder().CreateFCmpONE(value,
                                         llvm::ConstantFP::get(value->getType(), 0.0),
                                         "tmp.bool");
        return cmp;
    }
    return ctx_.builder().CreateBitCast(value, targetType, "bitcast.tmp");
}

llvm::Value *Emitter::emitNumericBinary(const std::string &op,
                                        llvm::Value *lhs,
                                        llvm::Value *rhs,
                                        bool isFloat) {
    if (isFloat) {
        if (op == "+") {
            return ctx_.builder().CreateFAdd(lhs, rhs, "fadd.tmp");
        }
        if (op == "-") {
            return ctx_.builder().CreateFSub(lhs, rhs, "fsub.tmp");
        }
        if (op == "*") {
            return ctx_.builder().CreateFMul(lhs, rhs, "fmul.tmp");
        }
        if (op == "/") {
            return ctx_.builder().CreateFDiv(lhs, rhs, "fdiv.tmp");
        }
    } else {
        if (op == "+") {
            return ctx_.builder().CreateAdd(lhs, rhs, "add.tmp");
        }
        if (op == "-") {
            return ctx_.builder().CreateSub(lhs, rhs, "sub.tmp");
        }
    }
    return nullptr;
}

}  // namespace scriptum
