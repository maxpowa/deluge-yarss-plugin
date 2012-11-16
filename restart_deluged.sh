#!/bin/bash
# Used to quickly restart the server during development

killall deluged
#python setup.py bdist_egg
echo "##############################################################################################"
echo "Start deluge server ##########################################################################"
echo "##############################################################################################"
deluged -l ~/deluged.log -L info
 