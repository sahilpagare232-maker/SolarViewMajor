import csv
import math
import random

# ============================================================
# ROOF CONFIGURATION
# ============================================================

ROOF_WIDTH = 30.0          # metres
ROOF_LENGTH = 20.0         # metres
GRID_SPACING = 1.0         # metres

# Roof orientation and tilt
ROOF_AZIMUTH = 180.0       # degrees, 180 = South
ROOF_TILT = 10.0           # degrees


# ============================================================
# SOLAR PANEL CONFIGURATION
# ============================================================

PANEL_WIDTH = 2.0          # metres
PANEL_LENGTH = 1.0         # metres
PANEL_EFFICIENCY = 0.22    # 22%


# ============================================================
# TIME CONFIGURATION
# ============================================================

START_HOUR = 8
END_HOUR = 18
TIME_STEP = 1


# ============================================================
# WEATHER CONFIGURATION
# ============================================================

MIN_WEATHER_FACTOR = 0.70
MAX_WEATHER_FACTOR = 1.00


# ============================================================
# GENERATE PANEL CANDIDATE POSITIONS
# ============================================================

def generate_candidate_positions():

    positions = []

    x = 0.0

    while x + PANEL_WIDTH <= ROOF_WIDTH:

        y = 0.0

        while y + PANEL_LENGTH <= ROOF_LENGTH:

            positions.append({
                "x": round(x, 2),
                "y": round(y, 2)
            })

            y += GRID_SPACING

        x += GRID_SPACING

    return positions


# ============================================================
# SIMPLIFIED SOLAR ALTITUDE
# ============================================================

def calculate_solar_altitude(hour):

    """
    Simplified solar altitude model.

    This is only for synthetic-data generation.
    Later replace this with pvlib solar position calculation.
    """

    hour_angle = (hour - 12) * 15

    altitude = 90 - abs(hour_angle) * 3.5

    altitude = max(0, min(90, altitude))

    return round(altitude, 2)


# ============================================================
# SIMPLIFIED SOLAR AZIMUTH
# ============================================================

def calculate_solar_azimuth(hour):

    """
    Simplified solar azimuth.

    Approximation:
    Sunrise direction -> East
    Noon -> South
    Sunset -> West

    Later replace with pvlib.
    """

    if hour <= 12:

        # East -> South
        azimuth = 90 + (hour - 6) * 15

    else:

        # South -> West
        azimuth = 180 + (hour - 12) * 15

    azimuth = max(90, min(270, azimuth))

    return round(azimuth, 2)


# ============================================================
# CALCULATE IRRADIANCE
# ============================================================

def calculate_irradiance(hour):

    altitude = calculate_solar_altitude(hour)

    if altitude <= 0:
        return 0.0

    # Maximum solar irradiance at STC
    max_irradiance = 1000.0

    # Effect of sun altitude
    sun_factor = math.sin(
        math.radians(altitude)
    )

    # Weather variation
    weather_factor = random.uniform(
        MIN_WEATHER_FACTOR,
        MAX_WEATHER_FACTOR
    )

    irradiance = (
        max_irradiance
        * sun_factor
        * weather_factor
    )

    return round(irradiance, 2)


# ============================================================
# CALCULATE SHADOW FACTOR
# ============================================================

def calculate_shadow_factor(x, y, hour):

    """
    Temporary synthetic shadow model.

    1.0 = no shadow
    0.0 = complete shadow

    Later replace this with actual shadow
    calculation from the 3D building model.
    """

    shadow_factor = 1.0

    # Morning shadow
    if hour <= 10:

        if x > ROOF_WIDTH * 0.65:

            shadow_factor = random.uniform(
                0.3,
                0.7
            )

    # Afternoon shadow
    elif hour >= 15:

        if x < ROOF_WIDTH * 0.35:

            shadow_factor = random.uniform(
                0.3,
                0.7
            )

    # Small random shadow variations
    if random.random() < 0.05:

        shadow_factor = random.uniform(
            0.5,
            0.9
        )

    return round(shadow_factor, 3)


# ============================================================
# EFFECTIVE IRRADIANCE
# ============================================================

def calculate_effective_irradiance(
    irradiance,
    shadow_factor
):

    effective_irradiance = (
        irradiance
        * shadow_factor
    )

    return round(
        effective_irradiance,
        2
    )


# ============================================================
# CALCULATE PANEL POWER
# ============================================================

def calculate_panel_power(
    effective_irradiance
):

    panel_area = (
        PANEL_WIDTH
        * PANEL_LENGTH
    )

    power = (
        effective_irradiance
        * panel_area
        * PANEL_EFFICIENCY
    )

    return round(
        power,
        2
    )


# ============================================================
# GENERATE SYNTHETIC DATASET
# ============================================================

def generate_dataset():

    positions = generate_candidate_positions()

    rows = []

    sample_id = 0

    for hour in range(
        START_HOUR,
        END_HOUR + 1,
        TIME_STEP
    ):

        # Solar position
        solar_altitude = (
            calculate_solar_altitude(hour)
        )

        solar_azimuth = (
            calculate_solar_azimuth(hour)
        )

        # Irradiance
        irradiance = (
            calculate_irradiance(hour)
        )

        # Every possible panel position
        for position in positions:

            x = position["x"]
            y = position["y"]

            # Shadow
            shadow_factor = (
                calculate_shadow_factor(
                    x,
                    y,
                    hour
                )
            )

            # Irradiance after shadow
            effective_irradiance = (
                calculate_effective_irradiance(
                    irradiance,
                    shadow_factor
                )
            )

            # Panel power
            panel_power = (
                calculate_panel_power(
                    effective_irradiance
                )
            )

            rows.append({

                "sample_id": sample_id,

                # Roof geometry
                "roof_width_m": ROOF_WIDTH,
                "roof_length_m": ROOF_LENGTH,
                "roof_area_m2":
                    round(
                        ROOF_WIDTH * ROOF_LENGTH,
                        2
                    ),

                "roof_azimuth":
                    ROOF_AZIMUTH,

                "roof_tilt":
                    ROOF_TILT,

                # Panel candidate position
                "x": x,
                "y": y,

                # Sun position
                "hour": hour,
                "solar_azimuth":
                    solar_azimuth,

                "solar_altitude":
                    solar_altitude,

                # Solar conditions
                "irradiance_w_m2":
                    irradiance,

                "shadow_factor":
                    shadow_factor,

                "effective_irradiance_w_m2":
                    effective_irradiance,

                # Panel information
                "panel_width_m":
                    PANEL_WIDTH,

                "panel_length_m":
                    PANEL_LENGTH,

                "panel_efficiency":
                    PANEL_EFFICIENCY,

                # Output / reward
                "panel_power_w":
                    panel_power
            })

            sample_id += 1

    return rows


# ============================================================
# SAVE DATASET
# ============================================================

def save_dataset(rows):

    filename = "synthetic_solar_data.csv"

    fieldnames = [

        "sample_id",

        "roof_width_m",
        "roof_length_m",
        "roof_area_m2",
        "roof_azimuth",
        "roof_tilt",

        "x",
        "y",

        "hour",
        "solar_azimuth",
        "solar_altitude",

        "irradiance_w_m2",
        "shadow_factor",
        "effective_irradiance_w_m2",

        "panel_width_m",
        "panel_length_m",
        "panel_efficiency",

        "panel_power_w"
    ]

    with open(
        filename,
        "w",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(rows)

    print(
        f"Generated {len(rows)} samples."
    )

    print(
        f"Dataset saved as: {filename}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    dataset = generate_dataset()

    save_dataset(dataset)