#!/bin/bash

rm -r /NeoSectional/data/GFSMAV &
sudo wget https://www.weather.gov/source/mdl/MOS/GFSMAV.t06z -P /NeoSectional/data/
sleep 5
sudo mv /NeoSectional/data/GFSMAV.t06z /NeoSectional/data/GFSMAV

