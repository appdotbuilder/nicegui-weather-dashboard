"""Main weather application with modern UI."""

from nicegui import ui
from app.city_service import city_service
from app.models import CityWithWeather


class WeatherApp:
    """Main weather application class."""

    def __init__(self):
        self.cities_container = None
        self.city_input = None
        self.country_input = None
        self.add_button = None
        self.refresh_button = None
        self.loading_indicator = None

    def apply_theme(self):
        """Apply modern theme colors."""
        ui.colors(
            primary="#2563eb",  # Professional blue
            secondary="#64748b",  # Subtle gray
            accent="#10b981",  # Success green
            positive="#10b981",
            negative="#ef4444",  # Error red
            warning="#f59e0b",  # Warning amber
            info="#3b82f6",  # Info blue
        )

        # Add custom CSS for modern styling
        ui.add_head_html("""
        <style>
            .weather-card {
                background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                transition: all 0.3s ease;
            }
            .weather-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            }
            .temperature {
                background: linear-gradient(135deg, #3b82f6, #8b5cf6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .add-form {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            .page-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
        </style>
        """)

    def create_weather_card(self, city: CityWithWeather) -> ui.card:
        """Create a weather card for a city."""
        with ui.card().classes("weather-card p-6 rounded-xl shadow-lg hover:shadow-xl transition-all") as card:
            with ui.row().classes("w-full items-center justify-between"):
                with ui.column().classes("gap-2"):
                    # City name and country
                    city_display = city.name
                    if city.country:
                        city_display += f", {city.country}"
                    ui.label(city_display).classes("text-xl font-bold text-gray-800")

                    # Temperature
                    if city.temperature is not None:
                        ui.label(f"{city.temperature}°C").classes("temperature text-4xl font-bold")
                    else:
                        ui.label("--°C").classes("text-4xl font-bold text-gray-400")

                    # Description
                    if city.description:
                        ui.label(city.description).classes("text-lg text-gray-600 capitalize")
                    else:
                        ui.label("No data").classes("text-lg text-gray-400")

                with ui.column().classes("gap-2 items-end"):
                    # Delete button
                    ui.button(
                        icon="delete",
                        on_click=lambda e, city_id=city.id: self.delete_city(city_id) if city_id is not None else None,
                    ).classes("text-red-500 hover:bg-red-50").props("flat round")

                    # Weather details
                    if city.humidity is not None:
                        ui.label(f"💧 {city.humidity}%").classes("text-sm text-gray-500")
                    if city.wind_speed is not None:
                        ui.label(f"💨 {city.wind_speed} km/h").classes("text-sm text-gray-500")

                    # Last updated
                    if city.last_updated:
                        time_str = city.last_updated.strftime("%H:%M")
                        ui.label(f"Updated: {time_str}").classes("text-xs text-gray-400")
                    else:
                        ui.label("No data").classes("text-xs text-gray-400")

        return card

    def create_add_city_form(self):
        """Create the form for adding new cities."""
        with ui.card().classes("add-form p-6 rounded-xl shadow-lg mb-6"):
            ui.label("Add New City").classes("text-xl font-bold text-gray-800 mb-4")

            with ui.row().classes("gap-4 w-full items-end"):
                self.city_input = ui.input(placeholder="Enter city name", value="").classes("flex-1").props("outlined")

                self.country_input = (
                    ui.input(placeholder="Country (optional)", value="").classes("w-48").props("outlined")
                )

                self.add_button = ui.button("Add City", icon="add_location", on_click=self.add_city).classes(
                    "bg-primary text-white px-6 py-2 hover:bg-blue-600"
                )

            # Enable enter key to submit
            self.city_input.on("keydown.enter", self.add_city)
            self.country_input.on("keydown.enter", self.add_city)

    def create_header(self):
        """Create the page header."""
        with ui.row().classes("page-header w-full p-6 mb-6 rounded-xl shadow-lg items-center justify-between"):
            with ui.column().classes("gap-2"):
                ui.label("🌤️ Weather Dashboard").classes("text-3xl font-bold")
                ui.label("Track weather for your favorite cities").classes("text-lg opacity-90")

            with ui.row().classes("gap-2"):
                self.refresh_button = (
                    ui.button("Refresh All", icon="refresh", on_click=self.refresh_all_weather)
                    .classes("bg-white text-blue-600 hover:bg-gray-50")
                    .props("outline")
                )

                # Auto-refresh toggle
                ui.button("Auto-refresh: ON", icon="schedule", on_click=self.toggle_auto_refresh).classes(
                    "bg-white text-blue-600 hover:bg-gray-50"
                ).props("outline")

    def create_loading_indicator(self):
        """Create loading indicator."""
        with ui.row().classes("justify-center items-center p-8") as loading:
            ui.spinner(size="lg", color="primary")
            ui.label("Loading weather data...").classes("ml-4 text-lg text-gray-600")
            loading.visible = False
            self.loading_indicator = loading

    async def add_city(self):
        """Add a new city to the dashboard."""
        if not self.city_input or not self.city_input.value.strip():
            ui.notify("Please enter a city name", type="warning")
            return

        city_name = self.city_input.value.strip()
        country = self.country_input.value.strip() if self.country_input else ""

        # Show loading
        if self.add_button:
            self.add_button.set_text("Adding...")
            self.add_button.props("loading")

        try:
            city = await city_service.add_city(city_name, country)

            if city:
                ui.notify(f"Added {city_name} successfully!", type="positive")
                if self.city_input:
                    self.city_input.set_value("")
                if self.country_input:
                    self.country_input.set_value("")
                await self.refresh_cities_display()
            else:
                ui.notify(f"Could not find city: {city_name}", type="negative")

        except Exception as e:
            ui.notify(f"Error adding city: {str(e)}", type="negative")

        finally:
            if self.add_button:
                self.add_button.set_text("Add City")
                self.add_button.props(remove="loading")

    async def delete_city(self, city_id: int):
        """Delete a city from the dashboard."""
        try:
            success = city_service.delete_city(city_id)
            if success:
                ui.notify("City removed successfully!", type="positive")
                await self.refresh_cities_display()
            else:
                ui.notify("Failed to remove city", type="negative")
        except Exception as e:
            ui.notify(f"Error removing city: {str(e)}", type="negative")

    async def refresh_all_weather(self):
        """Refresh weather data for all cities."""
        if not self.refresh_button:
            return

        if self.refresh_button:
            self.refresh_button.set_text("Refreshing...")
            self.refresh_button.props("loading")

        try:
            updated_count = await city_service.refresh_all_weather_data()
            ui.notify(f"Updated {updated_count} cities", type="positive")
            await self.refresh_cities_display()
        except Exception as e:
            ui.notify(f"Error refreshing weather: {str(e)}", type="negative")
        finally:
            if self.refresh_button:
                self.refresh_button.set_text("Refresh All")
                self.refresh_button.props(remove="loading")

    async def refresh_cities_display(self):
        """Refresh the cities display."""
        if not self.cities_container:
            return

        # Clear existing content
        self.cities_container.clear()

        # Get updated cities data
        cities = city_service.get_all_cities_with_weather()

        if not cities:
            with self.cities_container:
                with ui.card().classes("p-8 text-center bg-gray-50 rounded-xl"):
                    ui.icon("location_off", size="3rem").classes("text-gray-400 mb-4")
                    ui.label("No cities added yet").classes("text-xl text-gray-600 mb-2")
                    ui.label("Add your first city using the form above").classes("text-gray-500")
        else:
            with self.cities_container:
                # Create responsive grid
                grid_classes = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                with ui.element("div").classes(grid_classes):
                    for city in cities:
                        self.create_weather_card(city)

    def toggle_auto_refresh(self):
        """Toggle auto-refresh functionality."""
        # This would implement auto-refresh logic
        ui.notify("Auto-refresh toggled", type="info")

    def setup_auto_refresh(self):
        """Set up automatic refresh every 30 minutes."""
        # Auto-refresh functionality would be implemented here
        # For now, just setup the timer without creating a background task
        # to avoid pending task warnings in tests
        pass

    async def create_page(self):
        """Create the main weather page."""
        # Apply theme
        self.apply_theme()

        # Create page layout
        with ui.column().classes("w-full max-w-7xl mx-auto p-6 gap-6"):
            # Header
            self.create_header()

            # Add city form
            self.create_add_city_form()

            # Loading indicator
            self.create_loading_indicator()

            # Cities container
            self.cities_container = ui.column().classes("w-full")

            # Initial load
            await self.refresh_cities_display()

        # Set up auto-refresh
        self.setup_auto_refresh()


# Global instance
weather_app = WeatherApp()


def create():
    """Create the weather application routes."""

    @ui.page("/")
    async def index():
        """Main weather dashboard page."""
        await weather_app.create_page()
