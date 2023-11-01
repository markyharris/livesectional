# LiveSectional.com

<head>
    <link rel="stylesheet" href='/static/style-v4.css' />
</head>
<body>
     <p class="lead">
	This code has been updated to 4.5xx which uses the new FAA API. A new image will be uploaded to www.livesectional.com that encorporates this change.
	Visit https://www.livesectional.com/community/postid/1377/ for information on fixing the outage caused by FAA on 10/18/2023. Code here will be updated.<p>
        Version v4 of LiveSectional adds many new features for builders to take advantage of. Visit <a class="text-danger" href="http://livesectional.com" target="_blank">livesectional.com</a> for build and software installation instructions.
        <ul>
          <li>Updated to run under <a class="text-danger" href="https://docs.python.org/3/howto/pyporting.html" target="_blank">Python 3.7</a>
          <li>Added the ability to display <a class="text-danger" href="https://aviationweather.gov/taf/decoder" target="_blank">TAF (Terminal Aerodrome Forecasts)</a>.
          <li>Added the ability to display <a class="text-danger" href="https://www.weather.gov/mdl/mos_home" target="_blank">MOS (Model Output Statistics)</a>. Only available for the United States and its Territories.
          <li>Added the ability to decode METARs from weather stations not located on airports, such as KMYP - 	Monarch Pass, CO. (Thank you Nick C.)
          <li>Heat Map was added to display what airports have been landed at, and how often. Home airport can be designated.
	     <li>Added the ability to install a rotary switch so viewer can select what data to display, METAR's, TAF's, MOS or Heat Map.
          <li>If rotary switch is not installed, the software can set a default data to display. i.e. METAR's.
          <li>Sleep Timer - The Map can be put to sleep at night (or anytime) if desired. Pressing a pushbutton will turn on temporarily.
          <li>Reload the config settings automatically. The map will restart and reload the settings when new settings are saved.
          <li>Map builder has the ability to use both types of LED's, either RGB and/or GRB color encoding on same map.
          <li>Decodes the airport ID to show City and State. If international airports are used, it will show Site and Country. 
          <li>Will display IP address if an LCD/OLED display is used.
	     <li>Logging capabilities were added to help with diagnosing issues.
          <li>The builder can now download and backup the config file, airports file, Heat Map file and logfile.
          <li>The builder can import a config file and airports file to make maintenance and upgrading easier.
          <li>Wind direction can now be displayed using an arrow or numbers in degrees and includes Gusts as well.
          <li>The user interface was improved to optimize for mobile applications.
          <li>Config Profiles available to load to help start the configuration process.
          <li>Many new Transitional Wipes were added for when the FAA weather is being updated. Some are still a work in process.
          <li>Ability to setup wifi remotely through the use of Android or IPhone app thanks to  <a class="text-danger" href="http://berrylan.org" target="_blank">Berrylan.org</a>.
          <li>A System Information page was added to help with diagnosis if necessary. 
          <li>A Phone App was added to allow the casual user to control the data displayed on the map if a Rotary Switch was not installed. (Thank you Lance B.)
          <li>To help the casual user to access the App, a 'Create QR Code' feature was added to Utilities to display next to the map.
          <li>Added the ability to set the RPI's Time Zone without needing to enter the command line.
          <li>Added the ability to expand RPI's file system without needing to enter the command line.
          <li>Added the ability to rotate OLED display 180 degrees, and to reverse the position order of OLED's due to build constraints.
          <li>Added a Map Layout page that will provide a graphical representation of the map design and LED routing.
          <li>Added ability for more than 300 airports on a single map. Thank you Daniel.
          <li>Increased the max number of airports from 500 to 3000 in 'Basic Settings'
        </ul>
    </p>
  <hr>
    <p class="lead">
        Browser Compatibility: The following browsers have been tested and found to work (4-2020).        
        <ul>
          <li>Windows 10
          <ul>
            <li>Chrome: Recommended, as most development was done using Chrome.
            <li>Microsoft Edge: All functions work.
            <li>Firefox: All functions work.
            <li>Internet Explorer: All functions work, (except range sliders on Heat Map Editor).   
            <li>Opera: All functions work.
          </ul>
          <li>IPAD - IOS 13
          <ul>
            <li>Chrome: All functions work.
            <li>Safari: All functions work.
          </ul>
          <li>Android 9
          <ul>
            <li>Chrome: All functions work.
            <li>Miren Browser: All functions work.    
          </ul>
          <li>Mac 10.15 Catalina
          <ul>
            <li>Safari: All functions work.
            <li>Chrome: All functions work.
            <li>Firefox: All functions work.
            <li>Opera: All functions work.
          </ul>
        </ul>
    </p>
  <hr>
    <p class="lead">
	There are 3 editors that will help set up the software for the map;
	<ul>
	  <li>Settings Editor - Use this editor to set up all the settings for the builder's map.
	  <li>Airports Editor - Use to create the airports file specific to the builder's map.
	  <li>Heat Map Editor - Use this to set which airports have been landed at, and how often.
	</ul>
    </p>
  <hr>
    <p class="lead">
        There are 2 other menus;
        <ul>
          <li>Map Functions
	  <ul>
	     <li>Turn On Map - Turn's on the map and displays.
	     <li>Turn Off Map - Turn's off the map and displays.
	     <li>Reboot RPI - Will force the Raspberry Pi to reboot.
	     <li>Shutdown RPI - Will power down the Raspberry Pi.
	     <li>Map Layout - Displays the airports layed out on a map.
             </ul>
          <li>Map Utilities
          <ul>
             <li>Homepage - Will bring up the Home page.
             <li>Set RPI Timezone - Allows the user to set their Time Zone without the command line.
             <li>Expand File System - Allows RPI to utilize the entire amount of memory on the microSD Card.
             <li>Download Config File - Allows the builder to backup the config file to another computer.         
             <li>Download Airports File - Allows the builder to backup the airports file to another computer.
             <li>Download Heat Map File - Allows the builder to download Heat Map file for diagnostic purposes.
             <li>Download Logfile File - Allows the builder to download logfile for diagnostic purposes.                  
             <li>Run LED Test Script - Run a basic test script to check all the LED's.
             <li>Run OLED Test Script - Run a basic test script to check the OLED displays.
             <li>Web Remote App - Setup for the casual user to control the type of weather data displayed on the map.
             <li>Create QR Code for Web Remote - Creates a QR Code to display for users to run phone app.
             <li>View Schematics - Opens new web page with access to the various Schematics helpful for building.
             <li>System Information - Opens new web page and displays information about the system, RPI and OS.
             <li>Update History - Lists the various versions along with the updates made.
             <li>Help - Opens a new web page and loads the Help page of LiveSectional.com.
            </ul>
        </ul>
    </p>
  <hr>
    <p class="lead">
        The software was written to provide a myriad of build combinations. Below is a short list of combinations.
        <ul>
	  <li>Basic LED Map
	     <ul>
              <li>Basic LED Map Only - No other hardware other than an RPI and LED string.
              <li>Basic LED Map with Pushbuttons - Add up to 3 pushbuttons for reboot/power-off, data refresh and power-on.
              <li>Basic LED Map with Pushbuttons and Rotary Switch - The addition of the rotary switch gives the viewer the 
	          ability to choose what to display, METAR data, TAF data, MOS data or Heat Map.
	     </ul>
	  <li>LED Map with Display 
             <ul>
              <li>LED Map with LCD display - Use a 16x2 LCD to display Wind Speed and Direction information.
	      <li>LED Map with single OLED display - Use a single SSD1306 OLED display to show the same information.
              <li>LED Map with multiple OLED displays - Use up to 8 SSD1306 OLED displays to create a great display of data.
              <li>LED Map with display and Rotary Switch - The addition of the rotary switch gives the viewer the
                  ability to choose what to display, METAR data, TAF data, MOS data or Heat Map. Displays will show what data 
		  is being displayed, along with local and zulu time if desired.
	     </ul>
	  <li>Map with Legend - Legend can be added on any of the above maps if desired.
	     <ul>
              <li>Basic Legend - Will use 5 LED's to demonstrate VFR, MVFR, IFR, LIFR and No Weather reported.	
	      <li>High Winds and Lightning Legend - Will add 2 more LED's demonstrating High Winds and Lightning.
	      <li>Reported Weather Legend - Will require up to 5 more LED's to demonstrate reported weather including;
		  Rain, Freezing Rain, Snow, Dust/Ash/Sand, Fog.
	     </ul>
	  <li>Map with Light Sensor - An ambient light sensor can be added to any of the builds above and will 
              dim LED's when room lights are turned off.        
        </ul>
    </p>
 
  <hr>

  <blockquote class="blockquote">
  <p><b>Modified MIT License</b></p>

  <p>Copyright (c) 2022, 2023 Bill Bryson III and Mark Harris</p>

  <p>Permission is hereby granted, free of charge, to any person obtaining a copy
     of this software and associated documentation files (the Software), to deal
     in the Software without restriction, including without limitation the rights
     to use, copy, modify, merge, publish, distribute, sublicense, and to permit
     persons to whom the Software is furnished to do so, subject to the following conditions:</p>

  <p>The software may NOT be sold or distributed on its own, or with other products
     for sale without express permission from the author.
     Visit; http://www.livesectional.com/contact/ to contact the author.</p>

  <p>The above copyright notice and this permission notice shall be included in all
     copies or substantial portions of the Software.</p>

  <p>THE SOFTWARE IS PROVIDED AS IS, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
     IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
     FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
     AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
     LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
     OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
     SOFTWARE.</p>
  </blockquote>
</div>
</section>
</div>
</body>
