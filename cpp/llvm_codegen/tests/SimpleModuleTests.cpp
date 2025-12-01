#include "gtest/gtest.h"

#include "scriptum/SimpleModule.h"

using scriptum::SimpleFunction;
using scriptum::SimpleModuleEmitter;
using scriptum::SimpleReturn;

TEST(SimpleModuleEmitterTest, EmitsLiteralReturn) {
    SimpleFunction fn;
    fn.name = "principalis";
    fn.ret.isBinary = false;
    fn.ret.lhs = 3.0;

    SimpleModuleEmitter emitter("literal_mod");
    emitter.addFunction(fn);
    const auto ir = emitter.render();
    EXPECT_NE(ir.find("define double @principalis()"), std::string::npos);
    EXPECT_NE(ir.find("ret double 3.000000e+00"), std::string::npos);
}

TEST(SimpleModuleEmitterTest, EmitsBinaryAddition) {
    SimpleFunction fn;
    fn.name = "soma";
    fn.ret.isBinary = true;
    fn.ret.lhs = 1.0;
    fn.ret.rhs = 2.0;

    SimpleModuleEmitter emitter("sum_mod");
    emitter.addFunction(fn);
    const auto ir = emitter.render();
    EXPECT_NE(ir.find("fadd double 1.000000e+00, 2.000000e+00"), std::string::npos);
}
