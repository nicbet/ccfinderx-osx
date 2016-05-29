#include "ccfxconstants.h"

#include <boost/cstdint.hpp>
#include <boost/array.hpp>

const boost::array<boost::int32_t, 4> APPVERSION = { 10, 2, 7, 3 };

#if defined OS_WIN32
const std::string PLATFORM_NAME = "Windows XP x86";
#elif defined OS_UBUNTU
const std::string PLATFORM_NAME = "Ubuntu i386";
#elif defined OS_LINUX 
const std::string PLATFORM_NAME = "Linux";
#elif defined OS_MACOSX
const std::string PLATFORM_NAME = "MacOSX x64";
#else
#error
#endif

