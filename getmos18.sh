#!/bin/bash

rm -f /NeoSectional/data/GFSMAV 
sudo wget https://www.weather.gov/source/mdl/MOS/GFSMAV.t18z -P /NeoSectional/data/
sleep 5
sudo mv /NeoSectional/data/GFSMAV.t18z /NeoSectional/data/GFSMAV
