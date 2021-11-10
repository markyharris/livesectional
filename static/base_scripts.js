function get_badge(ap,loc) {
  var xhttp = new XMLHttpRequest();
  var outp = "";
  var vis_in_miles = "";
  var sky_condition = "";
  var sky_ceiling = "";
  var flightcategory = "VFR";
  var rawMessage = "";
  
  xhttp.onreadystatechange = function() {
  if (this.status == 404) {
    console.log('Undefined Airport');
    rawMessage = 'The Airport ID entered is Undefined. Please Check ID';
    flightcategory = "UNDF";
  }

  if (this.readyState == 4 && this.status == 200) {
    //console.log(xhttp.responseText); 
    
 
    obj = JSON.parse(xhttp.responseText);
    rawMessage = obj.properties.rawMessage;
    if (rawMessage == "") {
      rawMessage = "No METAR Data Returned by FAA API. CLICK for Raw METAR"; 
      flightcategory = "NOWX";
    }

    console.log(obj.properties.rawMessage);
    console.log("Num of Layers "+obj.properties.cloudLayers.length);
    vis_in_miles = (parseInt(obj.properties.visibility.value)*3.28084/5280).toFixed(2);
      
    for (var i = 0; i < obj.properties.cloudLayers.length; i++) {
      console.log(obj.properties.cloudLayers[i].base.value);      
      console.log(obj.properties.cloudLayers[i].amount); 
        sky_condition = obj.properties.cloudLayers[i].amount;
        sky_ceiling = Math.round(obj.properties.cloudLayers[i].base.value*3.28084);

      if (sky_condition=="OVC" || sky_condition=="BKN" || sky_condition=="OVX" || sky_condition=="VV") {
          console.log("-->"+sky_condition);
          console.log("-->"+sky_ceiling);
                  
          if (sky_ceiling < 500) {
              flightcategory = "LIFR";
          } else if (sky_ceiling >= 500 && sky_ceiling < 1000) {
              flightcategory = "IFR";
          } else if (sky_ceiling >= 1000 && sky_ceiling <= 3000) {
              flightcategory = "MVFR";
          } else if (sky_ceiling > 3000) {
              flightcategory = "VFR";
          }

          if (flightcategory != "VFR") { 
              break; 
          }                    
      }
    }  
        
  if (flightcategory != "LIFR") {
      if (vis_in_miles < 1) {
          flightcategory = "LIFR";
      } else if (vis_in_miles >= 1.0 && vis_in_miles < 3.0) {
          flightcategory = "IFR";
      } else if (vis_in_miles >= 3.0 && vis_in_miles <= 5.0) {
          flightcategory = "MVFR";
      }                         
    }

    console.log(flightcategory);                         
    console.log("Vis = "+vis_in_miles+" miles");      

  }
      
  outp = '<a href="https://www.aviationweather.gov/metar/data?ids='+ap+'&format=decoded&hours=0&taf=on&layout=on" target="_blank">';
  if (flightcategory == 'VFR') {
    var outp = outp + '<h6><span class="badge badge-success">';
    } else if (flightcategory == 'MVFR') {
    var outp = outp + '<h6><span class="badge badge-primary">';
    } else if (flightcategory == 'IFR') {
    var outp = outp + '<h6><span class="badge badge-danger">';
    } else if (flightcategory == 'LIFR') {
    var outp = outp + '<h6><span class="badge-lifr">';
    } else if (flightcategory == 'NOWX') {
    var outp = outp + '<h6><span class="badge-nowx">';
    } else if (flightcategory == 'UNDF') {
    var outp = outp + '<h6><span class="badge-undf">';
    }    

  outp = outp + '&nbsp'+flightcategory+'&nbsp</span>&nbsp-&nbsp'+rawMessage+'</h6></a>';        
  document.getElementById(loc).innerHTML = outp;                         
};
    
xhttp.open("GET", "https://api.weather.gov/stations/"+ap+"/observations/latest", true);
xhttp.send();
}

 
<!-- Script to grab Flight Category from www.checkwx.com. Limited number of hits per day. Must in HEAD-->
function get_fc(ap,loc) {
  var xhttp = new XMLHttpRequest();
  var outp = ""

  xhttp.onreadystatechange = function() {
  if (this.readyState == 4 && this.status == 200) {
    console.log(xhttp.responseText);
    obj = JSON.parse(xhttp.responseText);

      if (obj.data[0].flight_category == 'VFR') {
        var outp = '<a href="https://www.checkwx.com/weather/'+ap+'/metar" target="_blank"><h5><p class="badge badge-success">'
        } else if (obj.data[0].flight_category == 'MVFR') {
        var outp = '<a href="https://www.checkwx.com/weather/'+ap+'/metar" target="_blank"><h5><p class="badge badge-primary">'
        } else if (obj.data[0].flight_category == 'IFR') {
        var outp = '<a href="https://www.checkwx.com/weather/'+ap+'/metar" target="_blank"><h5><p class="badge badge-danger">'
        } else if (obj.data[0].flight_category == 'LIFR') {
        var outp = '<a href="https://www.checkwx.com/weather/'+ap+'/metar" target="_blank"><h5><p class="badge badge-warning">'
        }
      outp = outp + '&nbsp'+obj.data[0].flight_category+'&nbsp</p></h5></a>'
    document.getElementById(loc).innerHTML = outp
  }
};

xhttp.open("GET", "https://api.checkwx.com/metar/"+ap+"/decoded", true);
xhttp.setRequestHeader('X-API-Key', '106e449c03ae4ec6af47581ff9');
xhttp.send();
}


<!-- Script to grab raw METAR data only from api.weather.gov-->    
function get_raw(ap,loc) {
  var xhttp = new XMLHttpRequest();
  var outp = ""
  
  xhttp.onreadystatechange = function() {
  if (this.readyState == 4 && this.status == 200) {
    //console.log(xhttp.responseText);      
    obj = JSON.parse(xhttp.responseText); 
    console.log(obj.properties.rawMessage);      
    document.getElementById(loc).innerHTML = obj.properties.rawMessage       
  }
};
    
xhttp.open("GET", "https://api.weather.gov/stations/"+ap+"/observations/latest", true);
xhttp.send();
}

