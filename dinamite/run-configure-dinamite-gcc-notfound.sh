#!/bin/bash

if [ "$OSTYPE" == 'darwin' ]; then
    echo "Configuring for OS X"
    INST_LIB=${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library DYLD_LIBRARY_PATH="${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library" LDFLAGS="-L${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library" LIBS="-linstrumentation"  CFLAGS="-O3 -g -Xclang -load -Xclang ${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/Release+Asserts/lib/AccessInstrument.dylib" CC="clang" ../configure --enable-snappy
else
    echo "Configuring for Unix"
    COMPILER_PATH=/usr/lib/gcc/x86_64-amazon-linux/4.8.3 INST_LIB=${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library LD_LIBRARY_PATH="${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library:${HOME}/Work/DINAMITE/LLVM/build/lib" LDFLAGS="-L${HOME}/Work/DINAMITE/LLVM/build/lib -L/usr/lib/gcc/x86_64-amazon-linux/4.8.3 -L${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library" LIBS="-linstrumentation -lpthread"  CFLAGS="-O3 -g -Xclang -load -Xclang ${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/Release+Asserts/lib/AccessInstrument.so" CC="clang" ../configure --enable-snappy
fi
echo "Don't forget to fix the libtool!"
