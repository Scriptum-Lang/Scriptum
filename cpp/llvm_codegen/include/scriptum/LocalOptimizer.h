#pragma once

#include <llvm/IR/Value.h>

namespace scriptum {

class LocalOptimizer {
public:
    llvm::Value *foldBinary(const std::string &op, llvm::Value *lhs, llvm::Value *rhs);
};

}  // namespace scriptum
