# Python script using "py_mini_racer" to test JavaScript logic functions.
from py_mini_racer import py_mini_racer

ctx = py_mini_racer.MiniRacer()

# Injecting JavaScript functions.
ctx.eval("""

function formatHour(timestamp) {
    const date = new Date(timestamp);
    let hours = date.getHours();
    const ampm = hours >= 12 ? "PM" : "AM";
    hours = hours % 12 || 12;
    return hours + " " + ampm;
}

function searchStations(stations, query) {
    query = query.toLowerCase().trim();
    return stations.filter(station => station.name.toLowerCase().includes(query));
}

function groupBikeDataByHour(bikeData, stationNumber) {
    const hourly = {};
    bikeData.filter(row => row.number == stationNumber).forEach(row => {
        const date = new Date(row.last_update);
        const hour = date.getHours();
        if (!hourly[hour]) hourly[hour] = [];
        hourly[hour].push(row.available_bikes);
    });
    const result = {};
    Object.keys(hourly).forEach(h => {
        const avg = hourly[h].reduce((a, b) => a + b, 0) / hourly[h].length;
        result[h] = Math.round(avg);
    });
    return result;
}

function aggregateHourlyWeather(data) {
    const grouped = {};
    data.forEach(row => {
        const date = new Date(row.last_update);
        const hour = date.getHours();
        if (!grouped[hour]) {
            grouped[hour] = {
                temps: [], feels_like: [], humidity: [], wind_speed: [], description: row.description
            };
        }
        grouped[hour].temps.push(row.temperature);
        grouped[hour].feels_like.push(row.feels_like);
        grouped[hour].humidity.push(row.humidity);
        grouped[hour].wind_speed.push(row.wind_speed);
    });

    const avg = arr => Math.round(arr.reduce((a, b) => a + b, 0) / arr.length);
    const result = {};
    Object.keys(grouped).forEach(hour => {
        const g = grouped[hour];
        result[hour] = {
            temperature: avg(g.temps),
            feels_like: avg(g.feels_like),
            humidity: avg(g.humidity),
            wind_speed: avg(g.wind_speed),
            description: g.description
        };
    });
    return result;
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
""")

# Python test functions below.

# Testing "formatHour()", to check if timestamp is correctly converted to 12 hour format.
def test_format_hour():
    print("\n[formatHour]")
    for ts in ["2025-04-14T00:00:00", "2025-04-14T13:00:00", "2025-04-14T12:00:00"]:
        result = ctx.call("formatHour", ts)
        print(f"  Input: {ts} Output: {result}")
    assert ctx.call("formatHour", "2025-04-14T00:00:00") == "12 AM"
    assert ctx.call("formatHour", "2025-04-14T13:00:00") == "1 PM"
    assert ctx.call("formatHour", "2025-04-14T12:00:00") == "12 PM"

# Testing "searchStations()", to check that the search logic is case insensitive and filters correctly by partial name.
def test_search_stations():
    print("\n[searchStations]")
    stations = [
        {"name": "Smithfield"},
        {"name": "College Green"},
        {"name": "Pearse Street"}
    ]
    result = ctx.call("searchStations", stations, "college")
    print("  Query: 'college' Result:", [s["name"] for s in result])
    assert result[0]["name"] == "College Green"

# Testing "groupBikeDataByHour()", by validating grouping of bike data by hour and average.
def test_group_bike_data_by_hour():
    print("\n[groupBikeDataByHour]")
    data = [
        {"number": 1, "available_bikes": 5, "last_update": "2025-04-14T08:15:00"},
        {"number": 1, "available_bikes": 7, "last_update": "2025-04-14T08:45:00"},
        {"number": 1, "available_bikes": 3, "last_update": "2025-04-14T09:00:00"},
        {"number": 2, "available_bikes": 8, "last_update": "2025-04-14T08:00:00"}
    ]
    result = ctx.call("groupBikeDataByHour", data, 1)
    print("  Output:", result)
    assert result["8"] == 6
    assert result["9"] == 3

# Testing "aggregateHourlyWeather()", by checking averages.
def test_aggregate_hourly_weather():
    print("\n[aggregateHourlyWeather]")
    data = [
        {"last_update": "2025-04-14T08:00:00", "temperature": 10, "feels_like": 9, "humidity": 80, "wind_speed": 5, "description": "Clear"},
        {"last_update": "2025-04-14T08:30:00", "temperature": 12, "feels_like": 10, "humidity": 85, "wind_speed": 6, "description": "Clear"}
    ]
    result = ctx.call("aggregateHourlyWeather", data)
    print("  Output:", result)
    assert result["8"]["temperature"] == 11
    assert result["8"]["humidity"] == 83
    assert result["8"]["description"] == "Clear"

# Testing "getWeatherIcon()", by checking icon selection logic based on different weather conditions.
def test_get_weather_icon():
    print("\n[getWeatherIcon]")
    cases = ["clear sky", "light rain", "cloudy", "thunderstorm", "snow showers", "fog"]
    for c in cases:
        icon = ctx.call("getWeatherIcon", c)
        print(f"  Description: {c} Icon: {icon}")
    assert ctx.call("getWeatherIcon", "clear sky") == '<i class="fas fa-sun"></i>'
    assert ctx.call("getWeatherIcon", "light rain") == '<i class="fas fa-cloud-rain"></i>'
    assert ctx.call("getWeatherIcon", "cloudy") == '<i class="fas fa-cloud"></i>'
    assert ctx.call("getWeatherIcon", "thunderstorm") == '<i class="fas fa-bolt"></i>'
    assert ctx.call("getWeatherIcon", "snow showers") == '<i class="fas fa-snowflake"></i>'
    assert ctx.call("getWeatherIcon", "fog") == '<i class="fas fa-cloud"></i>'

# Running tests.
if __name__ == "__main__":
    test_format_hour()
    test_search_stations()
    test_group_bike_data_by_hour()
    test_aggregate_hourly_weather()
    test_get_weather_icon()
    print("\nTesting successful.")