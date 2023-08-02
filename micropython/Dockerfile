FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    build-essential \
    git

WORKDIR /usr/local/src

RUN git clone --depth=1 --branch=v1.20.0 --recurse-submodules --shallow-submodules https://github.com/micropython/micropython.git

# TODO: version fix
RUN git clone --depth=1 https://github.com/spatialdude/usqlite.git

WORKDIR /usr/local/src/micropython

RUN apt-get install -y \
    gcc-arm-none-eabi \
    cmake \
    python3

RUN make -C mpy-cross

WORKDIR /usr/local/src/micropython/ports/rp2

RUN make BOARD=PICO_W submodules
RUN make BOARD=PICO_W clean
RUN make BOARD=PICO_W USER_C_MODULES=../../../usqlite/micropython.cmake
