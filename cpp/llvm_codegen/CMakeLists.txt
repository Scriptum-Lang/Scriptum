cmake_minimum_required(VERSION 3.16)
project(scriptum_llvm_codegen_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(LLVM REQUIRED CONFIG)
message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")

include(FetchContent)
FetchContent_Declare(
    pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11.git
    GIT_TAG v2.12.0
)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(pybind11 googletest)

include_directories(${LLVM_INCLUDE_DIRS})
add_definitions(${LLVM_DEFINITIONS})

file(GLOB SCRIPTUM_CODEGEN_SOURCES
    src/CodegenContext.cpp
    src/Emitter.cpp
    src/Visitors.cpp
    src/LocalOptimizer.cpp
    src/SimpleModule.cpp
)

add_library(scriptum_codegen_llvm_cpp STATIC ${SCRIPTUM_CODEGEN_SOURCES})
target_include_directories(scriptum_codegen_llvm_cpp PUBLIC include)
llvm_map_components_to_libnames(LLVM_LIBS support core irreader)
target_link_libraries(scriptum_codegen_llvm_cpp PUBLIC ${LLVM_LIBS})

pybind11_add_module(scriptum_codegen_llvm_cpp_py src/bindings.cpp)
target_include_directories(scriptum_codegen_llvm_cpp_py PRIVATE include)
target_link_libraries(scriptum_codegen_llvm_cpp_py PRIVATE scriptum_codegen_llvm_cpp)

enable_testing()
add_executable(scriptum_codegen_llvm_cpp_tests tests/SimpleModuleTests.cpp)
target_include_directories(scriptum_codegen_llvm_cpp_tests PRIVATE include)
target_link_libraries(scriptum_codegen_llvm_cpp_tests PRIVATE scriptum_codegen_llvm_cpp GTest::gtest_main)
include(GoogleTest)
gtest_discover_tests(scriptum_codegen_llvm_cpp_tests)
