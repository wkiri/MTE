#!/bin/bash
# Set up for jSRE experiments

# Set the Java CLASSPATH
export JSREBASE=../../../jsre/jsre-1.1
export CLASSPATH=$JSREBASE/dist/xjsre.jar:`ls $JSREBASE/lib/commons*jar | tr '\012' ':'`:$JSREBASE/lib/libsvm-2.8.jar:$JSREBASE/lib/log4j-1.2.8.jar

echo "Java classpath is set."

# Check for jSRE config files
if [ ! -e jsre-config.xml ] ; then
    echo "Copying jsre-config.xml over."
    cp ../../../jsre/jsre-1.1/jsre-config.xml .
fi
if [ ! -e log-config.txt ] ; then
    echo "Copying log-config.txt over."
    cp ../../../jsre/jsre-1.1/log-config.txt .
fi

echo 
echo "Example training:"
echo "cat lpsc15/*element.examples > lpsc15/lpsc15-element.train"
echo "t=element; java -mx256M org.itc.irst.tcc.sre.Train -m 256 -k SL -c 1 lpsc15/lpsc15-\$t.{train,model}"

echo
echo "Example testing:"
echo "cat lpsc16/*element.examples > lpsc16/lpsc16-element.test"
echo "t=element; java -mx256M org.itc.irst.tcc.sre.Predict lpsc16/lpsc16-\$t.test lpsc15/lpsc15-\$t.model lpsc16/lpsc16-\$t.output"
