#!/bin/bash

rm -r /NeoSectional/GFSMAV &
sudo wget https://www.weather.gov/source/mdl/MOS/GFSMAV.t06z -P /NeoSectional/
sleep 5
sudo mv /NeoSectional/GFSMAV.t06z /NeoSectional/GFSMAV

