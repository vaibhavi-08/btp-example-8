from app.convertor import (
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    kelvin_to_celsius,
)


def main():
    print(celsius_to_fahrenheit(25))
    print(fahrenheit_to_celsius(77))
    print(kelvin_to_celsius(300))


if __name__ == "__main__":
    main()
