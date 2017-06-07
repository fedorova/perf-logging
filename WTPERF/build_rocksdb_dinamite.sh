export ROCKSDB="$HOME/Work/rdb/rocksdb"

export DIN_FILTERS="$ROCKSDB/func_filters.json"
export DIN_MAPS="$ROCKSDB/DINAMITE_MAPS"

export CPATH=/usr/local/include
export LIBRARY_PATH=/usr/local/lib

export CXX=clang++
export EXTRA_CFLAGS="-isystem /usr/lib/gcc/x86_64-amazon-linux/4.8.3/../../../../include/c++/4.8.3 -O3 -g -v -Xclang -load -Xclang $LLVM_SOURCE/Release+Asserts/lib/AccessInstrument.so -I/usr/include/c++/4.8.3/x86_64-amazon-linux -I/usr/local/include -DGFLAGS=google" 
export EXTRA_CXXFLAGS=$EXTRA_CFLAGS
export EXTRA_LDFLAGS="-L$LLVM_SOURCE/projects/dinamite/library/ -linstrumentation -L/usr/lib/gcc/x86_64-amazon-linux/4.8.3 -L/usr/local/lib -lgflags"

#make clean
make db_bench
