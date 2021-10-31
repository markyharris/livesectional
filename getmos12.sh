#!/bin/bash

rm -f /NeoSectional/data/GFSMAV
sudo wget https://www.weather.gov/source/mdl/MOS/GFSMAV.t12z -P /NeoSectional/data/
sudo mv /NeoSectional/data/GFSMAV.t12z /NeoSectional/data/GFSMAV
