#!/bin/bash

rm -r /NeoSectional/GFSMAV &
sudo wget https://www.weather.gov/source/mdl/MOS/GFSMAV.t12z -P /NeoSectional/
sleep 5
sudo mv /NeoSectional/GFSMAV.t12z /NeoSectional/GFSMAV
