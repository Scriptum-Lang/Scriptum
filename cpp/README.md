# Scriptum LLVM Codegen (C++)

Este diret?rio abriga o backend experimental escrito em C++ que produz llvm::Module diretamente via API oficial. O backend textual em Python continua dispon?vel, mas scriptum run --backend=llvm-cpp j? consegue importar o binding gerado aqui e volta para a VM quando ele n?o estiver presente (mensagens claras explicam o fallback).

- CMakeLists.txt: configura a biblioteca est?tica (scriptum_codegen_llvm_cpp), o m?dulo pybind11 (scriptum_codegen_llvm_cpp_py) e os testes do GoogleTest (scriptum_codegen_llvm_cpp_tests). Pybind11/GoogleTest s?o baixados automaticamente via FetchContent.
- include/scriptum/: cabe?alhos do emissor m?nimo (SimpleModuleEmitter).
- src/: implementa??o do emissor + bindings (indings.cpp).
- 	ests/: su?te de regress?o em C++ (	ests/SimpleModuleTests.cpp).

## Como construir

`ash
python scripts/build_cpp_backend.py          # cmake + build + testes
# ou manualmente
cd cpp/llvm_codegen
cmake -S . -B build
cmake --build build --target scriptum_codegen_llvm_cpp_py scriptum_codegen_llvm_cpp_tests
ctest --output-on-failure
`

? necess?rio ter o LLVM instalado (pacotes llvm-dev/llvm-toolchain ou um build local) e expor LLVM_DIR ou llvm-config para o CMake. Ap?s o build, a CLI procura automaticamente o m?dulo em cpp/llvm_codegen/build; utilize SCRIPTUM_LLVM_CPP_PATH para apontar para diret?rios alternativos.
