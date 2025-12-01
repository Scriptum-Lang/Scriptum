#pragma once

#include <llvm/IR/Value.h>

#include <memory>

namespace scriptum {

class ExprNode;
class StmtNode;
class FunctionNode;

class ExprVisitor {
public:
    virtual ~ExprVisitor() = default;
    virtual llvm::Value *visitLiteral(const ExprNode &node) = 0;
    virtual llvm::Value *visitIdentifier(const ExprNode &node) = 0;
    virtual llvm::Value *visitBinary(const ExprNode &node) = 0;
    virtual llvm::Value *visitUnary(const ExprNode &node) = 0;
    virtual llvm::Value *visitCall(const ExprNode &node) = 0;
};

class StmtVisitor {
public:
    virtual ~StmtVisitor() = default;
    virtual void visitBlock(const StmtNode &node) = 0;
    virtual void visitIf(const StmtNode &node) = 0;
    virtual void visitWhile(const StmtNode &node) = 0;
    virtual void visitFor(const StmtNode &node) = 0;
    virtual void visitReturn(const StmtNode &node) = 0;
    virtual void visitVarDecl(const StmtNode &node) = 0;
    virtual void visitAssignment(const StmtNode &node) = 0;
};

class FunctionVisitor {
public:
    virtual ~FunctionVisitor() = default;
    virtual void visitFunction(const FunctionNode &node) = 0;
};

}  // namespace scriptum
