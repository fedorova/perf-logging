#!/bin/sh

INST_LIB=${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library DYLD_LIBRARY_PATH="${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library" LDFLAGS="-L${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library" LIBS="-linstrumentation"  CFLAGS="-O3 -g -Xclang -load -Xclang ${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/Release+Asserts/lib/AccessInstrument.dylib" CC="clang" ../configure --enable-snappy
