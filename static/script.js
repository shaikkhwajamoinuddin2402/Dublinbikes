document.addEventListener("DOMContentLoaded", () => {
  /*************************************************************
   * 1) Map Initialization & Tile Layers
   *************************************************************/
  const osmLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors"
  });

  const satelliteLayer = L.tileLayer("https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
    attribution: "© Esri, Maxar, Earthstar Geographics"
  });

  const map = L.map("map", {
    center: [53.3498, -6.2603],
    zoom: 13,
    layers: [osmLayer]
  });

  /*************************************************************
   * 2) Toggle Satellite View
   *************************************************************/
  let isSatellite = false;
  const toggleSatelliteBtn = document.getElementById("toggleSatelliteBtn");
  toggleSatelliteBtn.addEventListener("click", () => {
    if (!isSatellite) {
      map.removeLayer(osmLayer);
      map.addLayer(satelliteLayer);
      toggleSatelliteBtn.textContent = "Map View";
      isSatellite = true;
    } else {
      map.removeLayer(satelliteLayer);
      map.addLayer(osmLayer);
      toggleSatelliteBtn.textContent = "Satellite View";
      isSatellite = false;
    }
  });

  /*************************************************************
   * 3) Heatmap Setup using Leaflet.heat
   *************************************************************/
  let heatLayer;
  let heatmapVisible = true;

  function updateHeatmap() {
    const heatData = stationsData.map(s => {
      let intensity = 0.5;
      if (s.bike_stands > 0) {
        intensity = s.available_bikes / s.bike_stands;
      }
      return [s.position.lat, s.position.lng, intensity];
    });
    if (heatLayer) map.removeLayer(heatLayer);
    heatLayer = L.heatLayer(heatData, { radius: 25, blur: 15, maxZoom: 17 });
    map.addLayer(heatLayer);
  }

  const toggleHeatmapBtn = document.getElementById("toggleHeatmapBtn");
  toggleHeatmapBtn.addEventListener("click", () => {
    if (heatmapVisible) {
      map.removeLayer(heatLayer);
      toggleHeatmapBtn.textContent = "Show Heatmap";
      heatmapVisible = false;
    } else {
      map.addLayer(heatLayer);
      toggleHeatmapBtn.textContent = "Hide Heatmap";
      heatmapVisible = true;
    }
  });

  /*************************************************************
   * 4) Station Data, Markers, and Search
   *************************************************************/
  let stationsData = [];
  let markers = [];
  let selectedDestination = null;

  const JCDECAUX_API_KEY = "73d438ede71ddb620f39852e803a61811835fe3e";
  const stationsUrl = `https://api.jcdecaux.com/vls/v1/stations?contract=dublin&apiKey=${JCDECAUX_API_KEY}`;

  fetch(stationsUrl)
    .then(response => {
      if (!response.ok) throw new Error("Network response not ok: " + response.statusText);
      return response.json();
    })
    .then(data => {
      stationsData = data;
      stationsData.forEach(station => {
        const lat = station.position.lat;
        const lng = station.position.lng;
        const marker = L.marker([lat, lng]).addTo(map);
        marker.bindPopup(`
          <strong>${station.name}</strong><br>
          Bikes: ${station.available_bikes}<br>
          Stands: ${station.available_bike_stands}
        `);
        markers.push({ station, marker });
      });
      updateHeatmap();
    })
    .catch(error => console.error("Error fetching station data:", error));

  const searchInput = document.getElementById("stationSearch");
  const searchBtn = document.getElementById("searchBtn");
  const searchResults = document.getElementById("searchResults");
  const stationSelect = document.getElementById("stationSelect");

  function handleSearch() {
    const query = searchInput.value.toLowerCase().trim();
    searchResults.innerHTML = "";
    if (!query) {
      searchResults.style.display = "none";
      return;
    }
    const filteredStations = stationsData.filter(station =>
      station.name.toLowerCase().includes(query)
    );
    if (filteredStations.length > 0) {
      searchResults.style.display = "block";
      filteredStations.forEach(station => {
        const li = document.createElement("li");
        li.textContent = station.name;
        li.addEventListener("click", () => {
          map.setView([station.position.lat, station.position.lng], 16);
          const markerObj = markers.find(m => m.station.number === station.number);
          if (markerObj) markerObj.marker.openPopup();
          selectedDestination = station;
          updateBikeChartForStation(station.number);
          stationSelect.value = station.number;
          searchResults.innerHTML = "";
          searchResults.style.display = "none";
          searchInput.value = station.name;
        });
        searchResults.appendChild(li);
      });
    } else {
      searchResults.style.display = "none";
    }
  }

  searchInput.addEventListener("keyup", handleSearch);
  searchBtn.addEventListener("click", handleSearch);

   /*************************************************************
   * 5) Get Directions Using Leaflet Routing Machine
   *     (With integrated "close" button in the routing control)
   *************************************************************/
   const getDirectionsBtn = document.getElementById("getDirectionsBtn");

   // Helper function: show route and add a close icon into routing control.
   function showRouteToStation(selectedStation) {
     if (!selectedStation) {
       alert("Please select a station.");
       return;
     }
     if (!navigator.geolocation) {
       alert("Geolocation is not supported by your browser.");
       return;
     }
     navigator.geolocation.getCurrentPosition(
       position => {
         const userLatLng = L.latLng(position.coords.latitude, position.coords.longitude);
         const destLatLng = L.latLng(selectedStation.position.lat, selectedStation.position.lng);
 
         // Remove any existing routing control.
         if (window.routingControl) {
           map.removeControl(window.routingControl);
         }
 
         // Create routing control using OSRM.
         window.routingControl = L.Routing.control({
           waypoints: [userLatLng, destLatLng],
           routeWhileDragging: true,
           geocoder: L.Control.Geocoder.nominatim(),
           showAlternatives: false,
           lineOptions: {
             styles: [{ color: "blue", opacity: 0.8, weight: 5 }]
           },
           router: new L.Routing.OSRMv1({
             serviceUrl: "https://router.project-osrm.org/route/v1"
           })
         })
           .on("routesfound", function(e) {
             if (e.routes && e.routes.length > 0) {
               const summary = e.routes[0].summary;
               const distanceKm = (summary.totalDistance / 1000).toFixed(2);
               const timeMinutes = (summary.totalTime / 60).toFixed(2);
               alert(
                 "Route found:\nDistance: " + distanceKm + " km\nEstimated Time: " + timeMinutes + " minutes."
               );
 
               // Add a close ("X") icon to the routing control container.
               const container = window.routingControl.getContainer();
               if (!container.querySelector(".close-routing")) {
                 const closeBtn = document.createElement("button");
                 closeBtn.className = "close-routing";
                 closeBtn.textContent = "×";
                 // Style the close button (adjust as needed)
                 closeBtn.style.position = "absolute";
                 closeBtn.style.top = "5px";
                 closeBtn.style.right = "5px";
                 closeBtn.style.background = "red";
                 closeBtn.style.color = "white";
                 closeBtn.style.border = "none";
                 closeBtn.style.borderRadius = "50%";
                 closeBtn.style.width = "30px";
                 closeBtn.style.height = "30px";
                 closeBtn.style.cursor = "pointer";
                 closeBtn.addEventListener("click", () => {
                   map.removeControl(window.routingControl);
                   window.routingControl = null;
                 });
                 container.appendChild(closeBtn);
               }
             }
           })
           .addTo(map);
       },
       error => {
         alert("Error obtaining your location: " + error.message);
       }
     );
   }
 
   getDirectionsBtn.addEventListener("click", () => {
     if (!selectedDestination) {
       alert("Please select a station from the search suggestions or dropdown first.");
       return;
     }
     showRouteToStation(selectedDestination);
   });

  /*************************************************************
   * 6) Map Click: Zoom In
   *************************************************************/
  map.on("click", () => {
    map.setZoom(map.getZoom() + 1);
  });

  /*************************************************************
   * 7) CSV Integration for Bike Chart & Weather Trends
   *************************************************************/
  let bikeData = [];
  let weatherData = [];
  let csvStations = [];
  let hourlyWeatherData = {};

  const weatherModal = document.getElementById("weatherModal");
  const modalTitle = document.getElementById("modalTitle");
  const weatherDetails = document.getElementById("weatherDetails");
  const closeModal = document.getElementById("closeModal");

  // Format timestamp to a 12-hour time string
  function formatHour(timestamp) {
    const date = new Date(timestamp);
    let hours = date.getHours();
    const ampm = hours >= 12 ? "PM" : "AM";
    hours = hours % 12 || 12;
    return hours + " " + ampm;
  }

  // Populate dropdown with station list
  function populateStationDropdown(stations) {
    stationSelect.innerHTML = "";
    stations.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.number;
      opt.textContent = s.name;
      stationSelect.appendChild(opt);
    });
    stationSelect.addEventListener("change", e => {
      updateBikeChartForStation(e.target.value);
      const st = stationsData.find(stn => stn.number == e.target.value);
      if (st) {
        map.setView([st.position.lat, st.position.lng], 16);
        const markerObj = markers.find(m => m.station.number === st.number);
        if (markerObj) markerObj.marker.openPopup();
        selectedDestination = st;
      }
    });
  }

  let bikeChart;
  function createBikeChart(labels, values) {
    const ctx = document.getElementById("bikeChart").getContext("2d");
    if (bikeChart) bikeChart.destroy();
    bikeChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "Available Bikes",
          data: values,
          borderColor: "#0077b6",
          backgroundColor: "#0077b6",
          fill: false,
          tension: 0.2,
          pointRadius: 5,
          pointHoverRadius: 7,
          borderWidth: 3
        }]
      },
      options: {
        responsive: true,
        scales: {
          x: { title: { display: true, text: "Hour of Day" } },
          y: { title: { display: true, text: "Available Bikes" }, beginAtZero: true }
        }
      }
    });
  }

  // Update Bike Chart using numeric hours
  function updateBikeChartForStation(stationNumber) {
    const filtered = bikeData.filter(row => row.number == stationNumber);
    const hourly = {};

    filtered.forEach(row => {
      const date = new Date(row.last_update);
      const numericHour = date.getHours();
      if (!hourly[numericHour]) hourly[numericHour] = [];
      hourly[numericHour].push(parseInt(row.available_bikes));
    });

    const sortedHours = Object.keys(hourly)
      .map(h => parseInt(h))
      .sort((a, b) => a - b);

    const labels = [];
    const values = [];
    sortedHours.forEach(h => {
      labels.push(h.toString().padStart(2, "0") + ":00");
      const avg = hourly[h].reduce((acc, val) => acc + val, 0) / hourly[h].length;
      values.push(Math.round(avg));
    });

    createBikeChart(labels, values);
  }

  function processWeatherHourly() {
    hourlyWeatherData = {};
    weatherData.forEach(row => {
      const hour = formatHour(row.last_update);
      if (!hourlyWeatherData[hour]) {
        hourlyWeatherData[hour] = {
          temps: [],
          feels_like: [],
          humidity: [],
          wind_speed: [],
          description: row.description
        };
      }
      hourlyWeatherData[hour].temps.push(+row.temperature);
      hourlyWeatherData[hour].feels_like.push(+row.feels_like);
      hourlyWeatherData[hour].humidity.push(+row.humidity);
      hourlyWeatherData[hour].wind_speed.push(+row.wind_speed);
    });

    const aggregated = {};
    Object.keys(hourlyWeatherData).forEach(hour => {
      const d = hourlyWeatherData[hour];
      const avg = arr => Math.round(arr.reduce((sum, val) => sum + val, 0) / arr.length);
      aggregated[hour] = {
        temperature: avg(d.temps),
        feels_like: avg(d.feels_like),
        humidity: avg(d.humidity),
        wind_speed: avg(d.wind_speed),
        description: d.description
      };
    });
    hourlyWeatherData = aggregated;
    createWeatherCards(hourlyWeatherData);
  }

   function createWeatherCards(data) {
    const container = document.getElementById("weatherCards");
    container.innerHTML = "";

    const parseHour = h => {
      const [hour, ap] = h.split(" ");
      let num = parseInt(hour);
      if (ap === "PM" && num !== 12) num += 12;
      if (ap === "AM" && num === 12) num = 0;
      return num;
    };

    const sortedKeys = Object.keys(data).sort((a, b) => parseHour(a) - parseHour(b));

    sortedKeys.forEach(hour => {
      const info = data[hour];
      const card = document.createElement("div");
      card.className = "weather-card";
      card.innerHTML = `
        <div class="card-time">${hour}</div>
        <div class="weather-icon">${getWeatherIcon(info.description)}</div>
        <div class="temperature">${info.temperature}°C</div>
      `;
      card.addEventListener("click", () => showWeatherDetails(hour));
      container.appendChild(card);
    });
  }


  function getWeatherIcon(description) {
    const desc = description.toLowerCase();
    if (desc.includes("rain")) return '<i class="fas fa-cloud-rain"></i>';
    if (desc.includes("clear")) return '<i class="fas fa-sun"></i>';
    if (desc.includes("cloud")) return '<i class="fas fa-cloud"></i>';
    if (desc.includes("thunder")) return '<i class="fas fa-bolt"></i>';
    if (desc.includes("snow")) return '<i class="fas fa-snowflake"></i>';
    return '<i class="fas fa-cloud"></i>';
  }

  function showWeatherDetails(hour) {
    const det = hourlyWeatherData[hour];
    if (!det) return;
    modalTitle.textContent = `Weather Details for ${hour}`;
    weatherDetails.innerHTML = `
      <div class="detail-label">Temperature:</div><div class="detail-value">${det.temperature}°C</div>
      <div class="detail-label">Feels Like:</div><div class="detail-value">${det.feels_like}°C</div>
      <div class="detail-label">Humidity:</div><div class="detail-value">${det.humidity}%</div>
      <div class="detail-label">Wind Speed:</div><div class="detail-value">${det.wind_speed} m/s</div>
      <div class="detail-label">Description:</div><div class="detail-value">${det.description}</div>
    `;
    weatherModal.style.display = "flex";
  }

  closeModal.addEventListener("click", () => {
    weatherModal.style.display = "none";
  });
  weatherModal.addEventListener("click", e => {
    if (e.target === weatherModal) weatherModal.style.display = "none";
  });

  /*************************************************************
   * 10) Load CSV Data via PapaParse
   *************************************************************/
  function loadCSVData() {
    Promise.all([
      fetch("/static/availability.csv").then(r => r.text()),
      fetch("/static/weather_data.csv").then(r => r.text()),
      fetch("/static/stations.csv").then(r => r.text())
    ]).then(([availCsv, wCsv, stCsv]) => {
      bikeData = Papa.parse(availCsv, { header: true, dynamicTyping: true }).data.filter(r => r.number);
      weatherData = Papa.parse(wCsv, { header: true, dynamicTyping: true }).data.filter(r => r.id && !isNaN(r.temperature));
      csvStations = Papa.parse(stCsv, { header: true }).data.filter(s => s.number);

      populateStationDropdown(csvStations);

      if (csvStations.length > 0) {
        updateBikeChartForStation(csvStations[0].number);
      }

      processWeatherHourly();
    }).catch(err => console.error("Error loading CSVs:", err));
  }

  loadCSVData();
});