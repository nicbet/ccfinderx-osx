#!/bin/bash

pushd `dirname $0`

java -Djava.library.path=/usr/lib/jni/:. -classpath /usr/lib/java/swt-gtk-3.5.jar:icu4j-4_0_1.jar:icu4j-charsets-4_0_1.jar:icu4j-localespi-4_0_1.jar:pathjson.jar:/usr/lib/java/trove-2.0.4.jar:.:gemxlib.jar GemXMain

popd
