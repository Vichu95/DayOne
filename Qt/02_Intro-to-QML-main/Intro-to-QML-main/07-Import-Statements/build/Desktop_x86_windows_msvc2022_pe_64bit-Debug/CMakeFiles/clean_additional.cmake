# Additional clean files
cmake_minimum_required(VERSION 3.16)

if("${CONFIG}" STREQUAL "" OR "${CONFIG}" STREQUAL "Debug")
  file(REMOVE_RECURSE
  "CMakeFiles\\IntroToQML_autogen.dir\\AutogenUsed.txt"
  "CMakeFiles\\IntroToQML_autogen.dir\\ParseCache.txt"
  "IntroToQML_autogen"
  )
endif()
