cmake_minimum_required(VERSION 3.13)
project(endplay)

# Global settings
# ===============
if (NOT CMAKE_BUILD_TYPE)
	set(CMAKE_BUILD_TYPE Release)
endif()
set(CMAKE_CXX_STANDARD 17)
set(ENDPLAY_ROOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/endplay")
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/VERSION" ENDPLAY_VERSION)


# Configure config.py with version number
# ==================
configure_file("${ENDPLAY_ROOT_DIR}/config.py.in" "config.py" @ONLY)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/config.py" DESTINATION ".")


# _dds library
# ============

# Compile the source files for the DDS library together into a shared library file
set(DDS_ROOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/libs/dds/")
set(DDS_SOURCE
	dds.cpp             dump.cpp            ABsearch.cpp
	ABstats.cpp         CalcTables.cpp      DealerPar.cpp
	File.cpp            Init.cpp            LaterTricks.cpp
	Memory.cpp          Moves.cpp           Par.cpp
	PlayAnalyser.cpp    PBN.cpp             QuickTricks.cpp
	Scheduler.cpp       SolveBoard.cpp      SolverIF.cpp
	System.cpp          ThreadMgr.cpp       Timer.cpp
	TimerGroup.cpp      TimerList.cpp       TimeStat.cpp
	TimeStatList.cpp    TransTableS.cpp     TransTableL.cpp)
if (CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
	set(DDS_SOURCE ${DDS_SOURCE} exports.def)
endif()
list(TRANSFORM DDS_SOURCE PREPEND "${DDS_ROOT_DIR}/src/")
add_library(dds SHARED ${DDS_SOURCE})
target_compile_definitions(dds PRIVATE 
	"DDS_THREADS_STL"
	"_CRT_SECURE_NO_WARNINGS"
)
target_include_directories(dds PRIVATE
	"${DDS_ROOT_DIR}/src"
)
# Compiler specific flags
if (CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
elseif (CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
	target_compile_options(dds PRIVATE "-Wno-format-overflow")
elseif (CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
	target_compile_definitions(dds PRIVATE "_CRT_SECURE_NO_WARNINGS")
	target_compile_options(dds PRIVATE "/wd4267")
else()
	message(WARNING "The compiler you are using hasn't been tested for building this library.")
endif()

# Read some hard-coded constants from the DDS header file to make sure that the
# ctypes bindings are compatible with the library we just compiled
file(READ "${DDS_ROOT_DIR}/include/dll.h" DDS_DLL_H)
string(REGEX MATCH "#define MAXNOOFBOARDS [0-9]+" DDS_MAXNOOFBOARDS "${DDS_DLL_H}")
string(REGEX MATCH "[0-9]+" DDS_MAXNOOFBOARDS "${DDS_MAXNOOFBOARDS}")
string(REGEX MATCH "#define MAXNOOFTABLES [0-9]+" DDS_MAXNOOFTABLES "${DDS_DLL_H}")
string(REGEX MATCH "[0-9]+" DDS_MAXNOOFTABLES "${DDS_MAXNOOFTABLES}")
configure_file("${ENDPLAY_ROOT_DIR}/_dds/__init__.py.in" "_dds/__init__.py" @ONLY)

# Install both bits into the right places in the package  
if (CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
	# .dll is a runtime component
	install(TARGETS dds RUNTIME DESTINATION "_dds")
else()
	install(TARGETS dds DESTINATION "_dds")
endif()

install(FILES "${CMAKE_CURRENT_BINARY_DIR}/_dds/__init__.py" DESTINATION "_dds/")