#!/bin/bash

DINAMITE_HOME=${HOME}/Work/DINAMITE/LLVM/llvm-3.5.0.src/projects/dinamite/library

if [ "$OSTYPE" == 'darwin' ]; then
    echo "Configuring for OS X"
    INST_LIB=${DINAMITE_HOME}  DYLD_LIBRARY_PATH="${DINAMITE_HOME}" LDFLAGS="-L${DINAMITE_HOME}" LIBS="-linstrumentation"  CFLAGS="-O3 -g -Xclang -load -Xclang ${DINAMITE_HOME}/../../../Release+Asserts/lib/AccessInstrument.dylib" CC="clang" ../configure --enable-snappy
else
    echo "Configuring for Unix"
    INST_LIB=${DINAMITE_HOME} LD_LIBRARY_PATH="${DINAMITE_HOME}:${HOME}/Work/LLVM/lib" LDFLAGS="-L${DINAMITE_HOME}" LIBS="-linstrumentation -lpthread"  CFLAGS="-O3 -g -Xclang -load -Xclang ${DINAMITE_HOME}/../../../Release+Asserts/lib/AccessInstrument.so" CC="clang" ../configure --enable-snappy
fi
echo "Don't forget to fix the libtool!"
