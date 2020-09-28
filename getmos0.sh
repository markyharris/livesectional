#!/bin/bash

rm -r /NeoSectional/GFSMAV &
sudo wget https://www.weather.gov/source/mdl/MOS/GFSMAV.t00z -P /NeoSectional/
sleep 5
sudo mv /NeoSectional/GFSMAV.t00z /NeoSectional/GFSMAV

