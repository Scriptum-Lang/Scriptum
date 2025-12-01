#include "scriptum/LocalOptimizer.h"

#include <llvm/IR/Constants.h>

namespace scriptum {

llvm::Value *LocalOptimizer::foldBinary(const std::string &op, llvm::Value *lhs, llvm::Value *rhs) {
    if (!llvm::isa<llvm::Constant>(lhs) || !llvm::isa<llvm::Constant>(rhs)) {
        return nullptr;
    }
    if (auto *lhsFP = llvm::dyn_cast<llvm::ConstantFP>(lhs)) {
        auto *rhsFP = llvm::dyn_cast<llvm::ConstantFP>(rhs);
        if (!rhsFP) {
            return nullptr;
        }
        if (op == "+") {
            return llvm::ConstantFP::get(lhsFP->getType(), lhsFP->getValueAPF() + rhsFP->getValueAPF());
        }
        if (op == "-") {
            return llvm::ConstantFP::get(lhsFP->getType(), lhsFP->getValueAPF() - rhsFP->getValueAPF());
        }
    }
    if (auto *lhsInt = llvm::dyn_cast<llvm::ConstantInt>(lhs)) {
        auto *rhsInt = llvm::dyn_cast<llvm::ConstantInt>(rhs);
        if (!rhsInt) {
            return nullptr;
        }
        if (op == "+") {
            return llvm::ConstantInt::get(lhsInt->getType(), lhsInt->getValue() + rhsInt->getValue());
        }
        if (op == "-") {
            return llvm::ConstantInt::get(lhsInt->getType(), lhsInt->getValue() - rhsInt->getValue());
        }
    }
    return nullptr;
}

}  // namespace scriptum
