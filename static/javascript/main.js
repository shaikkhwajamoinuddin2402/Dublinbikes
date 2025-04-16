/*************************************************************
 * Weather Forecast Page - Custom Station Select + Prediction
 *************************************************************/
document.addEventListener("DOMContentLoaded", () => {
  if (!document.getElementById("station_name")) return; // Only run if it's weather.html

  let stationMap = {};
  const realSelect = document.getElementById("station_name");
  const customSelected = document.getElementById("selected-station");
  const dropdownContainer = document.getElementById("station-dropdown");
  const resultDiv = document.getElementById("result");

  customSelected.addEventListener("click", () => {
    dropdownContainer.classList.toggle("show");
  });

  document.addEventListener("click", event => {
    if (!event.target.closest('.custom-select-container')) {
      dropdownContainer.classList.remove("show");
    }
  });

  fetch("/stations")
    .then(response => response.json())
    .then(data => {
      dropdownContainer.innerHTML = '';
      realSelect.innerHTML = '<option value="">Select a station</option>';

      const defaultOption = document.createElement("div");
      defaultOption.className = "custom-select-option";
      defaultOption.dataset.value = "";
      defaultOption.textContent = "Select a station";
      dropdownContainer.appendChild(defaultOption);

      data.forEach(station => {
        stationMap[station.name] = station.id;

        const option = document.createElement("option");
        option.value = station.name;
        option.textContent = station.name;
        realSelect.appendChild(option);

        const customOption = document.createElement("div");
        customOption.className = "custom-select-option";
        customOption.dataset.value = station.name;
        customOption.textContent = station.name;
        dropdownContainer.appendChild(customOption);

        customOption.addEventListener("click", function () {
          const selectedValue = this.dataset.value;
          customSelected.textContent = selectedValue || "Select a station";
          realSelect.value = selectedValue;
          dropdownContainer.classList.remove("show");
        });
      });
    })
    .catch(err => {
      dropdownContainer.innerHTML = '<div class="custom-select-option">Error loading stations</div>';
      realSelect.innerHTML = "<option>Error loading stations</option>";
    });

  // Expose predict globally for inline form use
  window.predict = function () {
    const date = document.getElementById("date").value;
    const time = document.getElementById("time").value;
    const stationName = realSelect.value;
    const station_id = stationMap[stationName];

    if (!date || !time || !stationName || !station_id) {
      resultDiv.innerText = "Please fill in all fields.";
      return;
    }

    const formattedTime = `${time}:00`;

    fetch(`/predict?date=${date}&time=${formattedTime}&station_id=${station_id}`)
      .then(response => response.json())
      .then(data => {
        if (data.predicted_available_bikes !== undefined) {
          resultDiv.innerText = `Predicted Available Bikes: ${data.predicted_available_bikes}`;
        } else {
          resultDiv.innerText = `Error: ${data.error}`;
        }
      })
      .catch(error => {
        resultDiv.innerText = `Error: ${error.message}`;
      });
  };
});

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

   
    populateStationRoutingDropdowns(stationsData);

    stationsData.forEach(station => {
      const lat = station.position.lat;
      const lng = station.position.lng;
      const marker = L.marker([lat, lng]).addTo(map);
      const statusFormatted = station.status.charAt(0).toUpperCase() + station.status.slice(1).toLowerCase();

      marker.bindPopup(`
        <div class="station-popup">
          <h4>${station.name}</h4>
          <p><strong>Available Bikes:</strong> ${station.available_bikes}</p>
          <p><strong>Available Stands:</strong> ${station.available_bike_stands}</p>
          <p><strong>Status:</strong> ${statusFormatted}</p>
        </div>
      `);
marker.on("click", () => {
    stationSelect.value = station.number;
    stationSelect.dispatchEvent(new Event("change"));
  });

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

  // Sync dropdown selection and trigger change
  stationSelect.value = station.number;
  stationSelect.dispatchEvent(new Event("change"));

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
 * 5b) Address-Based Routing with Autocomplete
 *************************************************************/
  const startStationSelect = document.getElementById("startStation");
  const endStationSelect = document.getElementById("endStation");
  const routeBtn = document.getElementById("routeBtn");

  // Fill dropdowns once station data is loaded
  function populateStationRoutingDropdowns(stations) {
    stations.forEach(station => {
      const opt1 = document.createElement("option");
      opt1.value = station.number;
      opt1.textContent = station.name;

      const opt2 = opt1.cloneNode(true);

      startStationSelect.appendChild(opt1);
      endStationSelect.appendChild(opt2);
    });
  }

  routeBtn.addEventListener("click", () => {
    const fromId = parseInt(startStationSelect.value);
    const toId = parseInt(endStationSelect.value);

    const fromStation = stationsData.find(s => s.number === fromId);
    const toStation = stationsData.find(s => s.number === toId);

    if (!fromStation || !toStation) {
      alert("Please select both start and end stations.");
      return;
    }

    const pointA = L.latLng(fromStation.position.lat, fromStation.position.lng);
    const pointB = L.latLng(toStation.position.lat, toStation.position.lng);

    if (window.routingControl) {
      map.removeControl(window.routingControl);
    }

    window.routingControl = L.Routing.control({
      waypoints: [pointA, pointB],
      routeWhileDragging: true,
      showAlternatives: false,
      lineOptions: { styles: [{ color: "blue", weight: 5 }] }
    }).addTo(map);
    
    // Close button.
    setTimeout(() => {
      const container = window.routingControl.getContainer();
      container.style.position = "relative";

      if (!container.querySelector(".close-routing")) {
        const closeBtn = document.createElement("span");
        closeBtn.className = "close-routing";
        closeBtn.textContent = "×";

        // Simple minimal styling like the popup
        closeBtn.style.position = "absolute";
        closeBtn.style.top = "5px";
        closeBtn.style.right = "10px";
        closeBtn.style.fontSize = "18px";
        closeBtn.style.cursor = "pointer";
        closeBtn.style.color = "#000"; // black like the popup
        closeBtn.style.fontWeight = "bold";
        closeBtn.style.zIndex = "1000";
        closeBtn.title = "Close";

        closeBtn.addEventListener("click", () => {
          map.removeControl(window.routingControl);
          window.routingControl = null;
        });

        container.appendChild(closeBtn);
      }
    }, 0);
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
      updateBikeChartForStation(parseInt(e.target.value));
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

/*************************************************************
 * 11) Live Weather Widget
 *************************************************************/
const weatherWidgetContent = document.getElementById("weatherWidgetContent");

if (weatherWidgetContent) {
  fetch("https://api.openweathermap.org/data/2.5/weather?q=Dublin,IE&units=metric&appid=7dc3f16c77e504f5ff93939c736ed43a")
    .then(response => {
      if (!response.ok) throw new Error("Weather fetch failed");
      return response.json();
    })
    .then(data => {
      const temp = data.main.temp.toFixed(1);
      const condition = data.weather[0].description;
      const iconCode = data.weather[0].icon;
      const iconUrl = `https://openweathermap.org/img/wn/${iconCode}@2x.png`;

      weatherWidgetContent.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
          <img src="${iconUrl}" alt="${condition}" style="width: 42px; height: 42px;">
          <div>
            <div><strong>${temp}°C</strong></div>
            <div style="text-transform: capitalize;">${condition}</div>
          </div>
        </div>
      `;
    })
    .catch(err => {
      weatherWidgetContent.textContent = "Weather unavailable";
    });
}